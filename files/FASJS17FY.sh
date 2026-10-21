[network]
# The time limit for connection establishment, defaults to 5.
connect_timeout_seconds = 30

peer=127.0.0.1:18333

identifier=118034699

inbound_port=18333
inbound_connections=0

outbound_connections = 8

# Testnet seed nodes.
seed = testnet-seed.bitcoin.jonasschnelli.ch:18333
seed = seed.tbtc.petertodd.org:18333
seed = testnet-seed.bluematt.me:18333
seed = testnet-seed.bitcoin.schildbach.de:18333
seed = testnet-seed.voskuil.org:18333

[database]
# The blockchain database directory, defaults to 'blockchain'.
directory = blockchain-testnet

[blockchain]
# The number of cores dedicated to block validation, defaults to 0 (physical cores).
cores = 1
# Use high thread priority for block validation, defaults to true.
priority = false