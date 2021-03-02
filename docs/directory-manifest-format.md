## Directory manifest file format

The directory manifest structure is as follows:

* `quorum`: integer representing the "quorum" (minimum number of trustees required for decryption)
* `trustee`: array of objects of the following form:
    * `id`: string representing the trustee's label
    * `sequence_number`: integer representing the order this trustee acts in during tallying
    * `address`: string representing the web address of this trustee
    * `public_key`: a representing the ECDSA verifying key for this trustee, in base 64. 