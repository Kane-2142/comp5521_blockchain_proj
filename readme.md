2022 Mar 27: Basic structure of blockchain server
<details><summary>Features table</summary>

| Function                                | Status        | Remarks       |
| ----------------                        | ------------- | ------------- |
| **Block Structure (3pts)**              |               |               |
|   - Index                               | Completed     |               |
|   - Timestamp                           | Completed     |               |
|   - Pre Block Hash                      | Completed     |               |
|   - Cur Block Hash                      | Completed     |               |
|   - Difficulty                          | Completed     |               |
|   - Nonce                               | Completed     |               |
|   - Merkle Root Trans                   | Completed     |               |
|   - Transaction data                    | Completed     |               |
| **Mining (3pts)**                       |               |               |
|   - Proof-of-work (2pts)                | Completed     |               |
|   - Dynamic Difficulty (1pts)           | Completed     |               |
| **Transaction (3pts, 1ea)**             |               |               |
|   - pay-to-public-key-hash (P2PKH)      | Completed     |               |
|   - signatures and verify trans         | Completed     |               |
|   - coinbase transaction                |               |               |
| **Network (3pts, 1ea)**                 |               |               |
|   - broadcast new blocks and get blocks |               |               |
|   - validate blocks                     | Partial       |               |
|   - longest chain rule when a fork      |               |               |
| **Storage (3pts, 1ea)**                 |               |               |
|   - store raw data in disk              |               |               |
|   - store state of blockchain in mem    |               |               |
|   - store UTXO in transaction pool      |               |               |
</details>

<details><summary>References</summary>
1. https://gruyaume.medium.com/create-your-own-blockchain-using-python-merkle-tree-pt-2-f84478a30690
2. https://gruyaume.medium.com/create-your-own-blockchain-using-python-transactions-and-security-pt-3-407e75d71acf
</details>
