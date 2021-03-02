## Client manifest file format

The client manifest structure is as follows:

* `directory:` string representing the web address of the directory server
* `device`: string representing the encryption device ID (see [the ElectionGuard specification](https://microsoft.github.io/electionguard-python/2_Encrypt_Ballots/#process) for more detail)
* `quorum`: integer representing the "quorum" (minimum number of trustees required for decryption)
* `trustee`: array of objects of the following form:
    * `id`: string representing this trustee's label
    * `sequence_number`: integer representing the order this trustee acts in during tallying
    * `address`: string representing the web address of this trustee
    * `public_key`: a representing the ECDSA verifying key for this trustee, in base 64
  
An example file can be found at `test/data/client-manifest.json`.