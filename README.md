# righttoask-directory
Directory server for the RightToAsk project. The directory stores information about the election and trustees, receives
client votes, and orchestrates distributed decryption with the trustees. It takes the form of a HTTP server hosting a
REST API. 

## Getting started
1. Create and activate a Python virtual environment. (**Note:** make sure you are using Python 3.8.x.)
```
 $ python3 --version
Python 3.8.2
 $ python3 -m venv venv      
 $ source venv/bin/activate
```
2. Install `poetry` (skip this step if you already have Poetry).
```
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```
3. Install the required Python packages. (May take a little while.)
```
poetry install
```

### Troubleshooting
* **Step 3:** `ERROR: Failed building wheel for cryptography`:
    * This is typically caused by libraries failing to link. Check that the following packages (or equivalent) are installed
      and available on your `PATH`:
        - `libssl-dev`
        - `libgmp-dev`
    
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

### `/tally`:
Run joint tallying and decryption, using the trustees. See [this repository](https://github.com/RightToAskOrg/righttoask-trustee) for more details.

**Returns:**
```json
{
  "success": true/false,
  "outcome": PlaintextTallyObject
}
```
where `PlaintextTallyObject` is an [ElectionGuard PlaintextTally](https://github.com/microsoft/electionguard-python/blob/main/src/electionguard/tally.py#L168).