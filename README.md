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
where `PlaintextTallyObject` is an [ElectionGuard PlaintextTally](https://github.com/microsoft/electionguard-python/blob/main/src/electionguard/tally.py#L168).
On failure:
```josn
{
  "success": false
}
```

To test this endpoint, use:
```shell
curl localhost:8000/tally
```

## Todo
* Documentation for directory and test client
* Documentation for manifest formats
* pydantic types for ElectionGuard
