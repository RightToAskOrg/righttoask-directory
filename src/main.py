import base64
import json
from typing import Tuple

import requests
import uvicorn

from electionguard.ballot import CiphertextBallot, BallotBoxState, from_ciphertext_ballot
from electionguard.decrypt_with_shares import decrypt_tally
from electionguard.decryption_share import TallyDecryptionShare
from electionguard.dlog import discrete_log
from electionguard.election import ElectionDescription, InternalElectionDescription, CiphertextElectionContext
from electionguard.election_builder import ElectionBuilder
from electionguard.group import g_pow_p, int_to_q
from electionguard.key_ceremony import ElectionJointKey
from electionguard.serializable import read_json, write_json
from electionguard.tally import CiphertextTally
from fastapi import FastAPI
from nacl import encoding
from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey
from pydantic import BaseModel


def load_trustee_manifest():
    with open("data/directory-manifest.json", "r") as file:
        return json.load(file)


def load_trustee_keys(data):
    result = dict()
    for trustee in data["trustees"]:
        object_id = trustee["id"]
        verify_key = VerifyKey(trustee["public_key"], encoder=encoding.Base64Encoder)
        result[object_id] = verify_key
    return result


def load_election_manifest():
    return ElectionDescription.from_json_file("data/election-manifest")


# Load the static information
trustee_data = load_trustee_manifest()
trustee_keys = load_trustee_keys(trustee_data)
election_desc = load_election_manifest()
ciphertexts = []

# For caching
_metadata = None
_context = None
_pubkey = None
_pubkey_sigs = dict()


def lazy_get_election() -> Tuple[InternalElectionDescription, CiphertextElectionContext]:
    """
    Lazily downloads the election public key from the trustees, and creates the appropriate election context.
    Caches once successful.
    :return: (metadata, context): the current election data, in ElectionGuard format
    """
    global _metadata
    global _context
    global _pubkey
    global _pubkey_sigs
    pubkeys = []

    if _metadata is None:
        for trustee in trustee_data["trustees"]:
            verify_key = trustee_keys[trustee["id"]]
            try:
                response = json.loads(requests.get(f"{trustee['address']}/pubkey").json())
            except requests.exceptions.ConnectionError:
                print(f"failed to connect to {trustee['id']}")
                continue

            pubkey = response["pubkey"]
            sig = response["signature"]

            try:
                verify_key.verify(base64.b64decode(sig) + write_json(pubkey).encode("utf-8"))
            except BadSignatureError:
                print(f"failed to verify signature for: {trustee['id']}")
                continue

            _pubkey_sigs[trustee["id"]] = sig
            pubkeys.append(pubkey)

        if len(pubkeys) == 0:
            raise Exception("no public key received")

        if len(set(pubkeys)) > 1:
            raise Exception("disagreement on the public key")

        _pubkey = read_json(pubkeys[0], ElectionJointKey)
        builder = ElectionBuilder(
            number_of_guardians=len(trustee_keys),
            quorum=trustee_data["quorum"],
            description=election_desc
        )
        builder.elgamal_public_key = _pubkey
        _metadata, _context = builder.build()

    return _metadata, _context


app = FastAPI()


@app.get("/trustees")
async def get_trustees():
    return trustee_data


@app.get("/election")
async def get_election():
    return write_json(election_desc)

@app.get("/pubkey")
async def get_pubkey():
    _, context = lazy_get_election()
    # ElectionGuard doesn't have a better encoding unfortunately
    return json.dumps({
        "pubkey": context.elgamal_public_key.to_hex()
    })


class Vote(BaseModel):
    body: str


@app.post("/vote")
async def post_vote(vote: Vote):
    ballot = read_json(vote.body, CiphertextBallot)
    ballot = from_ciphertext_ballot(ballot, BallotBoxState.CAST)
    ciphertexts.append(ballot)
    print("accepted ballot")
    return {}


@app.get("/tally")
async def run_tally():
    # TODO: cache this result?
    data = json.dumps({"body": write_json(ciphertexts)})
    metadata, context = lazy_get_election()

    # Get shares
    shares = dict()
    for trustee in trustee_data["trustees"]:
        try:
            response = json.loads(requests.get(f"{trustee['address']}/share", data=data).json())
        except requests.exceptions.ConnectionError:
            print(f"failed to connect to {trustee['id']}")
            continue

        share = read_json(json.dumps(response["share"]), TallyDecryptionShare)
        if share.guardian_id != trustee["id"]:
            print(f"share received from {trustee['id']} was for incorrect trustee {share.guardian_id}")
            continue

        # Check the signature
        sig = response["signature"]
        verify_key = trustee_keys[share.guardian_id]
        try:
            verify_key.verify(base64.b64decode(sig) + write_json(share).encode("utf-8"))
        except BadSignatureError:
            print(f"failed to verify signature for {share.guardian_id}")
            continue

        print(f"received share from {share.guardian_id}")
        shares[share.guardian_id] = share

    # TODO: compensate for missing shares

    tally = CiphertextTally("my-tally", metadata, context)
    tally.batch_append(ciphertexts)

    outcome = None
    if len(shares) == len(trustee_keys):
        outcome = decrypt_tally(tally, shares, context)

    if outcome is not None:
        return {"outcome": json.loads(write_json(outcome)), "success": True}
    else:
        return {"success": False}


if __name__ == "__main__":
    # Cannot run asyncio task while FastAPI is running, so pre-load it
    print("pre-loading discrete logarithm...")
    discrete_log(g_pow_p(int_to_q(1000000)))
    uvicorn.run("main:app", host="localhost", port=8000, loop="asyncio")
