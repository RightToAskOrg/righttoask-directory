import base64
import json
import sys
from uuid import uuid4

from electionguard import group
from electionguard.ballot import PlaintextBallot
from electionguard.election import ElectionDescription
from electionguard.election_builder import ElectionBuilder
from electionguard.encrypt import EncryptionDevice, EncryptionMediator
from electionguard.key_ceremony import ElectionJointKey
from electionguard.serializable import write_json, read_json
import requests
from electionguard.utils import get_optional


def load_client_manifest():
    # TODO: error checking
    with open("test/data/client-manifest.json", "r") as file:
        return json.load(file)


def parse_data():
    client_data = load_client_manifest()
    device_name: str = client_data["device"]
    directory_addr: str = client_data["directory"]
    count = len(client_data["guardians"])
    quorum: int = client_data["quorum"]

    # Load the election description
    try:
        election_desc = read_json(requests.get(f"{directory_addr}/election").json(), ElectionDescription)
        # Load the election public key
        pubkey_obj = json.loads(requests.get(f"{directory_addr}/pubkey").json())
        pubkey = get_optional(group.int_to_p(int(pubkey_obj["pubkey"], 16)))
    except requests.exceptions.ConnectionError:
        print(f"failed to connect to directory ({directory_addr})")
        exit(1)
        return

    builder = ElectionBuilder(
        number_of_guardians=count,
        quorum=quorum,
        description=election_desc
    )
    builder.elgamal_public_key = pubkey
    (metadata, context) = builder.build()
    return metadata, context, EncryptionDevice(device_name), directory_addr


def generate_ballot(vote: int):
    return PlaintextBallot.from_json_object({
        "object_id": str(uuid4()),
        "ballot_style": "righttoask-ballot-style",
        "contests": [
            {
                "object_id": "righttoask-contest",
                "ballot_selections": [
                    {
                        "object_id": "righttoask-upvote",
                        "vote": str(vote == 1)
                    },
                    {
                        "object_id": "righttoask-downvote",
                        "vote": str(vote == -1)
                    }
                ]
            }
        ]
    })


def main(vote: int):
    metadata, context, device, directory = parse_data()
    encrypter = EncryptionMediator(metadata, context, device)
    ballot = encrypter.encrypt(generate_ballot(vote))
    requests.post(f"{directory}/vote", data=json.dumps({"body": write_json(ballot)}))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python test/test-client.py <vote>")
        print("\twhere <vote> is 1 or -1")
    else:
        arg_vote = 0
        try:
            arg_vote = int(sys.argv[1])
            if arg_vote != 1 and arg_vote != -1:
                print("invalid vote (should be 1 or -1)")
                exit(1)
        except:
            print("invalid vote (should be a valid integer)")
            exit(1)

        main(arg_vote)
