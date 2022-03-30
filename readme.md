2022 Mar 27: Basic structure of blockchain server

Features table:
| Function            | Status        |
| ----------------    | ------------- |
| **Block Structure**     |               |
|   - Index            | Complete      |
|   - Timestamp        | Complete      |
|   - Pre Block Hash   | Complete      |
|   - Cur Block Hash   | Complete      |
|   - Dicfficulty      |               |
|   - Nonce            |               |
|   - Merkle Root Trans|               |
|   - Transaction data | Complete      |
| **Mining**                              |               |
|   - Proof-of-work                       | Complete      |
|   - Adv dyn. Difficulty                 |               |
| **Transaction**                         |               |
|   - pay-to-public-key-hash (P2PKH)      |               |
|   - signatures and verify trans         |               |
|   - coinbase transaction                |               |
| **Network**                             |               |
|   - broadcast new blocks and get blocks |               |
|   - validate blocks                     |               |
|   - longest chain rule when a fork      |               |
| **Storage**                             |               |
|   - store roaw data in disk             |               |
|   - store state of blockchain in mem    |               |
|   - store UTXO in transaction pool      |               |
