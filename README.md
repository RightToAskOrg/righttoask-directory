# righttoask-directory
Directory server for the RightToAsk project. The directory stores information about the election and trustees, receives
client votes, and orchestrates distributed decryption with the trustees. It takes the form of a HTTP server hosting a
REST API. 

## Getting started
1. Create and activate a Python virtual environment.
```
 $ python3 -m venv venv      
 $ source venv/bin/activate
```
2. Install `poetry` (skip this step if you already have Poetry).
```
$ curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
3. Ensure the required libraries are installed and available on your system:
   - `libssl-dev`
   - `libgmp-dev`
   - `libmpfr-dev`
4. Install the required Python packages. (May take a little while.)
```
$ poetry install
```
5. To run the directory, ensure you're in the virtual environment:
```bash
$ source venv/bin/activate
```
and run the server script:
```bash
$ python src/main.py
```
 
## API endpoints
### `/trustees`:
**Returns:** the trustee manifest, containing details about each trustee's name, address, sequence number, and public key.

### `/election`:
**Returns:** the election description, in [ElectionGuard format](https://microsoft.github.io/electionguard-python/Election_Manifest/).

### `/vote`:
**Request body:**
```json
{
  "body": "ciphertext-ballot"
}
```
Here `"ciphertext-ballot"` should be replaced with a stringified version of an [ElectionGuard CiphertextBallot](https://github.com/microsoft/electionguard-python/blob/main/src/electionguard/ballot.py#L638).
(TODO: this should be turned into a pydantic model eventually.)

For testing purposes, a lightweight client to submit votes is available at `test/test-client.py`. To use the test
client, ensure you're in the virtual environment and run
```shell
python test/test-client.py <vote>
```
where `<vote>` is `1` for an upvote or `-1` for a downvote.

### `/tally`:
Run joint tallying and decryption, using the trustees. See [this repository](https://github.com/RightToAskOrg/righttoask-trustee) for more details.

**Returns:**
On success:
```json
{
  "success": true,
  "outcome": PlaintextTallyObject
}
```
where `PlaintextTallyObject` is an [ElectionGuard PlaintextTally](https://github.com/microsoft/electionguard-python/blob/main/src/electionguard/tally.py#L168). The object contains both an upvote tally and a downvote tally.
On failure:
```json
{
  "success": false
}
```

To test this endpoint, use:
```shell
curl localhost:8000/tally
```

## File formats
Descriptions of the manifest formats used in this project are available in `docs/`. `election-manifest.json` is an
ElectionGuard format; more information [can be found here](https://microsoft.github.io/electionguard-python/0_Configure_Election/).

## Todo
* Documentation for directory server and test client code
* pydantic types for ElectionGuard.  Possible EG will do this.

### Important differences from final intended design

* There needs to be some care over how a decryption is initiated.  Clearly a plain API callable from anywhere is not the long term solution.  We need to avoid allowing the trustees to be usable as a decyrption oracle, and need to enforce rules about decryption occuring only on large sets of votes. 
* The recieved votes need to be in persistent storage rather than RAM.  A standard database (e.g. PostgeSQL) should be fine.
* Needs to be producing a "BB object", consisting of a verifiable proof a transcript, combined with inclusion proofs for individual data items; history proofs for prior checkpoints, etc.
* The directory probably needs to sign its responses.
* It also probably needs to sign its decryption requests to the trustees.
* Probably also needs to verify sigs from voters.  This is actually primarily for privacy, to deter stuffing with invalid votes and thus evading grouping for decryption.

### Troubleshooting and other details
When switching between talliers and directory, remember to deactivate one virtual environment ('deactivate' at command line) and then (re) activate the other.

422 Unprocessable entity: this error was encountered because of a mismatch between the expected and received types.  (one level of abstraction.)