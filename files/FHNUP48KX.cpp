#include <iostream>
#include <vector>
#include <string>
#include <cstdint>
#include <bitcoin/system.hpp>
#include <secp256k1.h>
 
 
// http://aaronjaramillo.org/libbitcoin-building-a-raw-transaction
// https://github.com/bitcoin/bips/blob/master/bip-0178.mediawiki
// the obvious stuff that should be covered by the usecase example would be
// (first out we do for P2PKH & P2SH, THEN we extend to all the other four: native & P2SH-wrapped P2WPKH & P2WSH):
/*
 
g++ \
    -std=c++11 \
    -o conceptual_usecase_script \
    conceptual_usecase_script.cpp \
    -fpermissive \
    $(pkg-config --cflags libbitcoin-system --libs libbitcoin-system) 
*/
 
using namespace bc; 
using namespace bc::system; 
using namespace bc::system::chain; 
using namespace bc::system::wallet; 
using namespace bc::system::machine; 
int main(int argc, char const *argv[])
{
    //  * (unrelated to segwit:) generate an HD wallet
    std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
    std::cout << std::endl << "* (unrelated to segwit:) generate an HD wallet" << std::endl;
    {
        data_chunk hd_entropy{16};
        pseudo_random_fill(hd_entropy);
        data_chunk hd_seed = to_chunk(decode_mnemonic(create_mnemonic(hd_entropy)));
        hd_private hd_private_key{hd_seed, hd_private::testnet};
        hd_public hd_public_key = hd_private_key.to_public();
 
        std::cout << "\nHd private key: " << std::endl;
        std::cout << hd_private_key.encoded() << std::endl;
        std::cout << "\nHd public key: " << std::endl;
        std::cout << hd_public_key.encoded() << std::endl;
 
        //  * Derive a pubkey from HD wallet
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* Derive a pubkey from HD wallet" << std::endl;
 
        hd_private child_private_key = hd_private_key.derive_private(1);
        std::cout << "\nChild Private key: " << std::endl;
        std::cout << child_private_key.encoded() << std::endl;
 
        hd_public child_public_key = hd_private_key.derive_public(1);
        std::cout << "\nChild Public key: " << std::endl;
        std::cout << child_public_key.encoded() << std::endl;
        
        // Produce P2PKH address from pubkey
        {
            payment_address child_testnet_p2pkh_address{child_public_key.point(), payment_address::testnet_p2kh};
            payment_address child_mainnet_p2pkh_address{child_public_key.point(), payment_address::mainnet_p2kh};
 
            std::cout << "\nChild testnet P2PKH address: " << std::endl;
            std::cout << child_testnet_p2pkh_address.encoded() << std::endl;
            std::cout << "\nChild mainnet P2PKH address: " << std::endl;
            std::cout << child_mainnet_p2pkh_address.encoded() << std::endl;   
        }
    
        // P2SH
        script child_script = operation::list{{opcode::push_positive_1}};
        payment_address child_testnet_p2sh_address{ script::to_pay_script_hash_pattern(
                            bitcoin_short_hash(child_script.to_data(false))), payment_address::testnet_p2sh};
        payment_address child_mainnet_p2sh_address{ script::to_pay_script_hash_pattern(
                            bitcoin_short_hash(child_script.to_data(false))), payment_address::mainnet_p2sh};
 
        std::cout << "\nChild testnet P2SH address: " << std::endl;
        std::cout << child_testnet_p2sh_address.encoded() << std::endl;
        std::cout << "\nChild mainnet P2SH address: " << std::endl;
        std::cout << child_mainnet_p2sh_address.encoded() << std::endl;   
    }
        
 
    //  * (unrelated to segwit:) generate a private key -> produce public key
    std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
    std::cout << "* (unrelated to segwit:) generate a private key -> produce public key" << std::endl;
    {
        ec_secret ec_secret_;
        secp256k1_context *ctx = secp256k1_context_create(SECP256K1_CONTEXT_VERIFY);
        do {
            pseudo_random::fill(ec_secret_);
        } while (0 == secp256k1_ec_seckey_verify(ctx, ec_secret_.data()));
        secp256k1_context_destroy(ctx);
 
 
        ec_private ec_testnet_private_key(to_chunk(ec_secret_), ec_private::testnet_p2kh);
        ec_private ec_mainnet_private_key(to_chunk(ec_secret_), ec_private::mainnet_p2kh);
 
        std::cout << std::endl << "\nEc private testnet key (WIF): " << std::endl;
        std::cout << ec_testnet_private_key.encoded() << std::endl;
        
        ec_public ec_public_key = ec_testnet_private_key.to_public();
        std::cout << "\nEc public testnet key:" << std::endl;
        std::cout << ec_public_key.encoded() << std::endl;
 
        std::cout << std::endl << "\nEc private mainnet key (WIF): " << std::endl;
        std::cout << ec_mainnet_private_key.encoded() << std::endl;
        
        // ec_public ec_public_key = ec_testnet_private_key.to_public();
        std::cout << "\nEc public mainnet key:" << std::endl;
        std::cout << ec_mainnet_private_key.to_public().encoded() << std::endl;
 
        //  * from a public key (and mainnet vs testnet choice), generate P2PKH address
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* from a public key (and mainnet vs testnet), generate P2PKH address" << std::endl;
        {
            ec_public ec_public_testnet_key{"020dac8dc99db8e7081645ca47bf2c4d3ba13f852c7ea341894b87212cf6215192"};
            payment_address testnet_p2pkh_address{ec_public_testnet_key.point(), payment_address::testnet_p2kh};
 
            std::cout << "\nEc public testnet key: " << std::endl;
            std::cout << ec_public_testnet_key.encoded() << std::endl;
            std::cout << "\nTestnet P2PKH address: " << std::endl;
            std::cout << testnet_p2pkh_address.encoded() << std::endl;
 
        }
        
        //  * parse P2PKH or P2SH address - confirm valid, confirm testnet vs mainnet, print binary dump of payload
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* parse P2PKH or P2SH address - confirm valid, confirm testnet vs mainnet, print binary dump of payload" << std::endl;
 
        {
            std::string string_address{"2N6XCVEPyAe7nddHSZuhs7gyZABXHHgEbcc"};
            payment_address testnet_address{string_address};
 
            if (testnet_address.version() == testnet_address.mainnet_p2kh) {
                std::cout << "\nMainnet Public key Hash" << std::endl;
            }
            else if (testnet_address.version() == testnet_address.mainnet_p2sh) {
                std::cout << "\nMainnet Script Hash" << std::endl;
            }
            else if (testnet_address.version() == testnet_address.testnet_p2kh) {
                std::cout << "\nTestnet Public key Hash" << std::endl;
            }
            else if (testnet_address.version() == testnet_address.testnet_p2sh) {
                std::cout << "\nTestnet Script Hash" << std::endl;
            }
            else {
                std::cout << "\nInvalid address format" << std::endl;
            }
 
            std::cout << testnet_address << std::endl;
        }
 
        //  * generate a Bitcoin TX output payload from a P2PKH or P2SH address
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* generate a Bitcoin TX output payload from a P2PKH or P2SH address" << std::endl;
 
        // P2PKH
        {
            payment_address testnet_p2pkh_address{"2N6XCVEPyAe7nddHSZuhs7gyZABXHHgEbcc"};
            std::cout << "\nOutput Testnet Address: " << std::endl;
            std::cout << testnet_p2pkh_address.encoded() << std::endl;
 
            script outputScript = script::to_pay_key_hash_pattern(bitcoin_short_hash(ec_public_key.point()));
 
            std::string BTC = "0.50";
            uint64_t Satoshis;
            decode_base10(Satoshis, BTC, 8);
            output p2pkh_output(Satoshis, outputScript);
 
            std::cout << "\nP2PKH Output p2sh_script: " << std::endl;
            std::cout << encode_base16(outputScript.to_data(false)) << std::endl;
            std::cout << p2pkh_output.script().to_string(0) << std::endl;
 
            std::cout << "\nAmount: " << encode_base10(p2pkh_output.value(), 8) << std::endl;
        }
        
        // P2SH
        {
            script p2sh_script = operation::list{{opcode::push_positive_1}};
            script outputScript = script::to_pay_script_hash_pattern(bitcoin_short_hash(p2sh_script.to_data(false)));
 
            std::string BTC = "0.50";
            uint64_t Satoshis;
            decode_base10(Satoshis, BTC, 8);
            output p2sh_output(Satoshis, outputScript);
 
            std::cout << "\nP2SH Output p2sh_script: " << std::endl;
            std::cout << encode_base16(outputScript.to_data(false)) << std::endl;
            std::cout << p2sh_output.script().to_string(0) << std::endl;
 
            std::cout << "\nAmount: " << encode_base10(p2sh_output.value(), 8) << std::endl;
        }
 
        //  * generate a Bitcoin TX input payload according to P2PKH template, from a private key, a TXID and output index
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* generate an unsigned Bitcoin TX input payload according to P2PKH template, from a private key, a TXID and output index" << std::endl;
 
        {
            payment_address testnet_p2pkh_address{ec_testnet_private_key};
            std::cout << "\nInput Testnet Address: " << std::endl;
            std::cout << testnet_p2pkh_address.encoded() << std::endl;
 
            script input_script = script::to_pay_key_hash_pattern(bitcoin_short_hash(ec_public_key.point()));
            
            hash_digest utxo_hash;
            if (!decode_base16(utxo_hash, "0f4488f6768fce01fe2104fbe4027609d0d7f2f5a0da50e68f4f317a96a85b4a"))
                std::cout << "Error: Hash not decoded properly! ***" << std::endl;
            uint32_t utxo_index = 0;
            
            input input_funding(output_point(utxo_hash, utxo_index), input_script, max_input_sequence);
 
            std::cout << "\nP2PKH Input p2sh_script: " << std::endl;
            std::cout << encode_base16(input_script.to_data(false)) << std::endl;
            std::cout << input_funding.script().to_string(0) << std::endl;
 
            std::cout << "\nP2PKH Input: " << std::endl;
            std::cout << encode_base16(input_funding.to_data()) << std::endl;
        }
    
        //  * generate an unsigned Bitcoin TX input payload according to P2SH template, from a script
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* generate an unsigned Bitcoin TX input payload according to P2SH template, from a script" << std::endl;
        {
            // hash160 [5c6f298919c020ae5a077988f30150d57be01283] equal
            script p2sh_script = operation::list{{opcode::push_positive_1}};
            script input_script = script::to_pay_script_hash_pattern(bitcoin_short_hash(p2sh_script.to_data(false)));
 
            hash_digest utxo_hash;
            if (!decode_base16(utxo_hash, "0f4488f6768fce01fe2104fbe4027609d0d7f2f5a0da50e68f4f317a96a85b4a"))
                std::cout << "Error: Hash not decoded properly! ***" << std::endl;
            uint32_t utxo_index = 0;
            input input_funding(output_point(utxo_hash, utxo_index), input_script, max_input_sequence);            
            std::cout << "\nP2SH TX input payload" << std::endl;
            std::cout << encode_base16(input_funding.to_data()) << std::endl;
        }
 
        //  * generate a Bitcoin TX, with one signed input according to P2PKH template, from a private key,
        //  a TXID and output index, and an output to a P2PKH address
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* generate a signed Bitcoin TX input payload according to P2PKH template, from a private key, a TXID and output index" << std::endl;
        {
            payment_address testnet_p2pkh_address{ec_testnet_private_key};
            std::cout << "\nInput Testnet Address: " << std::endl;
            std::cout << testnet_p2pkh_address.encoded() << std::endl;
 
            script input_script = script::to_pay_key_hash_pattern(bitcoin_short_hash(ec_public_key.point()));
            
            hash_digest utxo_hash;
            if (!decode_base16(utxo_hash, "0f4488f6768fce01fe2104fbe4027609d0d7f2f5a0da50e68f4f317a96a85b4a"))
                std::cout << "Error: Hash not decoded properly! ***" << std::endl;
            uint32_t utxo_index = 0;
            
            input input_funding(output_point(utxo_hash, utxo_index), input_script, max_input_sequence);
 
            output p2pkh_output{1000, script::to_pay_key_hash_pattern(bitcoin_short_hash(ec_public_key.point()))};
 
            input::list list_inputs = input::list{{input_funding}};
            output::list list_outputs = output::list {{p2pkh_output}};
 
            transaction tx{2, 0, list_inputs, list_outputs};
 
            endorsement sig;
            script p2pkh_script_code = script::to_pay_key_hash_pattern(bitcoin_short_hash(ec_public_key.point()));
 
            if(!script().create_endorsement(sig, ec_secret_, p2pkh_script_code, tx, 0,
                                        sighash_algorithm::all,  script_version::zero, 100000)) {
                std::cout << std::endl << "Error: error to create endorsement" << std::endl;
                return -1;
            }
 
            std::cout << "\nP2PKH Input p2pkh_script: " << std::endl;
            std::cout << encode_base16(input_script.to_data(false)) << std::endl;
            std::cout << input_funding.script().to_string(0) << std::endl;
 
            std::cout << "\nP2PKH Input: " << std::endl;
            std::cout << encode_base16(input_funding.to_data()) << std::endl;
 
            std::cout << "\nSignature: " << std::endl;
            std::cout << encode_base16(to_chunk(sig)) << std::endl;
 
 
            std::cout << "\nTransaction: " << std::endl;
            std::cout << encode_base16(tx.to_data(true,true)) << std::endl;
        }
 
        //  * generate a Bitcoin TX, with one signed input according to P2SH template, from a script, pushdata constants, a TXID and output index, and an output to a P2SH address
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* generate a Bitcoin TX, with one signed input according to P2SH template, from a script, pushdata constants, a TXID and output index, and an output to a P2SH address" << std::endl;
        {
            // hash160 [5c6f298919c020ae5a077988f30150d57be01283] equal
            script p2sh_script = operation::list{{opcode::push_positive_1}};
            script input_script = script::to_pay_script_hash_pattern(bitcoin_short_hash(p2sh_script.to_data(false)));
 
            hash_digest utxo_hash;
            if (!decode_base16(utxo_hash, "0f4488f6768fce01fe2104fbe4027609d0d7f2f5a0da50e68f4f317a96a85b4a"))
                std::cout << "Error: Hash not decoded properly! ***" << std::endl;
            uint32_t utxo_index = 0;
            input input_funding(output_point(utxo_hash, utxo_index), input_script, max_input_sequence);            
 
 
            output p2sh_output{1000, script::to_pay_script_hash_pattern(bitcoin_short_hash(p2sh_script.to_data(false)))};
 
            input::list list_inputs = input::list{{input_funding}};
            output::list list_outputs = output::list {{p2sh_output}};
 
            transaction tx{2, 0, list_inputs, list_outputs};
 
            endorsement sig;
            script p2sh_script_code = script::to_pay_script_hash_pattern(bitcoin_short_hash(p2sh_script.to_data(false)));
 
            if(!script().create_endorsement(sig, ec_secret_, p2sh_script_code, tx, 0,
                                        sighash_algorithm::all,  script_version::zero, 100000)) {
                std::cout << std::endl << "Error: error to create endorsement" << std::endl;
                return -1;
            }
 
            std::cout << "\nP2SH Input p2sh_script: " << std::endl;
            std::cout << encode_base16(input_script.to_data(false)) << std::endl;
            std::cout << input_funding.script().to_string(0) << std::endl;
 
            std::cout << "\nP2SH Input" << std::endl;
            std::cout << encode_base16(input_funding.to_data()) << std::endl;
 
            std::cout << "\nSignature: " << std::endl;
            std::cout << encode_base16(to_chunk(sig)) << std::endl;
 
            std::cout << "\nTransaction: " << std::endl;
            std::cout << encode_base16(tx.to_data(true,true)) << std::endl;
 
        }
 
 
        //  * check if an Bitcoin TX input or output payload matches the p2pkh or p2sh pattern
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* check if an Bitcoin TX input or output payload matches the p2pkh or p2sh pattern" << std::endl;
        {
            // REVIEW
            // this section, wha ti thought here would be, you inline a byte array that represents either a p2pkh or a p2sh input or output
            // maybe one of all four, plus one that's neither
            script p2sh_script = operation::list{{opcode::push_positive_1}};
            payment_address testnet_p2sh_address{script::to_pay_script_hash_pattern(bitcoin_short_hash(p2sh_script.to_data(false)))};
 
            script input_signature_script = script::to_pay_key_hash_pattern(bitcoin_short_hash(ec_public_key.point()));
            hash_digest utxo_hash;
            if (!decode_base16(utxo_hash, "0f4488f6768fce01fe2104fbe4027609d0d7f2f5a0da50e68f4f317a96a85b4a"))
                std::cout << "Error: Hash not decoded properly! ***" << std::endl;
            uint32_t utxo_index = 0;
            
            input p2wpkh_input_funding(output_point(utxo_hash, utxo_index), input_signature_script, max_input_sequence);
            script input_script = p2wpkh_input_funding.script();
            std::cout << input_script.to_string(0) << std::endl;
            
            if (script::is_pay_key_hash_pattern(input_script.operations()))
            {
                std::cout << "\nInput is P2PKH" << std::endl;
            }
            else if (script::is_pay_script_hash_pattern(input_script.operations()))
            {
                std::cout << "\nInput is P2SH" << std::endl;
            }
        }
        //  * extract Bitcoin address (always zero or one in count isn't it??) from Bitcoin TX input or output payload
        std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
        std::cout << "* extract Bitcoin address (always zero or one in count isn't it?) from Bitcoin TX input or output payload" << std::endl;
        // TODO Payment address extract methods
        {
            script p2sh_script = operation::list{{opcode::push_positive_1}};
            payment_address testnet_p2sh_address{script::to_pay_script_hash_pattern(bitcoin_short_hash(p2sh_script.to_data(false)))};
 
            script input_signature_script = script::to_pay_key_hash_pattern(bitcoin_short_hash(ec_public_key.point()));
            payment_address::list pay_list = payment_address::extract(input_signature_script, payment_address::testnet_p2kh, payment_address::testnet_p2sh);
            
            std::cout << "\nPayment address list size: " << pay_list.size() << std::endl;
            std::cout << "\nAddress list:" << std::endl;
 
            for(payment_address::list::iterator it = pay_list.begin(); it != pay_list.end(); it++)
            {
                std::cout << (*it).encoded() << std::endl;
            }
            
        }
    }
 
 
 
    //  * ??? WIF serialization ???
    std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
    std::cout << "* ??? WIF serialization ???" << std::endl;
 
    {
        data_chunk ec_secret_{16};
        secp256k1_context *ctx = secp256k1_context_create(SECP256K1_CONTEXT_VERIFY);
        do {
            pseudo_random_fill(ec_secret_);
        } while (!secp256k1_ec_seckey_verify(ctx, ec_secret_.data()));
        secp256k1_context_destroy(ctx);
 
        ec_private ec_testnet_private_key(ec_secret_, ec_private::testnet_p2kh);
        std::cout << std::endl << "\nWIF serialization of ec private key: " << std::endl;
        std::cout << ec_testnet_private_key.encoded() << std::endl;
        
        ec_public ec_public_key = ec_testnet_private_key.to_public();
        std::cout << "\nWIF serialization of ec public key: " << std::endl;
        std::cout << ec_public_key.encoded() << std::endl;
    }
 
    //  * ??? HD wallet xprv serialization ???
    std::cout << std::endl << std::endl << std::setw(40) << std::setfill('-') << "-" << std::endl;
    std::cout << "* ??? HD wallet xprv serialization ???" << std::endl;
    {
        data_chunk hd_entropy{16};
        pseudo_random_fill(hd_entropy);
        data_chunk hd_seed = to_chunk(decode_mnemonic(create_mnemonic(hd_entropy)));
        hd_private hd_private_key{hd_seed, hd_private::testnet};
        hd_public hd_public_key = hd_private_key.to_public();
 
        std::cout << "\nHd serialization of hd private key: " << std::endl;
        std::cout << hd_private_key.encoded() << std::endl;
        std::cout << "\nHd serialization of hd public key: " << std::endl;
        std::cout << hd_public_key.encoded() << std::endl;
        
    }
 
    //  * get list of transactions from txindex for given p2pkh/p2sh address
    {
        
    }
 
 
 
 
    // To clarify before we get productive:
 
    //  * Why on earth the wif & net flag in the ec_private class
 
    //    Hey! If I understood it correctly, ec_private is dealing with p2kh privkeys only, why? https://github.com/libbitcoin/libbitcoin-system/blob/00b1b1c5ebfcc91b8ad370fa9197f9ae93fb30fc/src/wallet/ec_private.cpp#L42-L48
 
    //    evoskuil [10:55 AM]
    //    You don't understand correctly :wink: These values are provided solely for payment address (and WIF) conversion. The class is more general than you assume.
    //    2 MIN AGO
 
    //  * What's the purpose with ec_private's ec_private ec_private::from_seed(const data_chunk& seed,uint8_t address_version) ?
 
 
    //  * Is WIF pubkey serialization actually supported for testnet??
    //    https://en.bitcoin.it/wiki/List_of_address_prefixes says 0xEF, but
    //     * not mentioned by https://github.com/libbitcoin/libbitcoin-system/blob/master/src/wallet/ec_public.cpp#L36
    //     * and https://github.com/bitcoin/bips/blob/master/bip-0178.mediawiki doesn't mention testnet
 
 
    // Notes about how needs to be implemented:
 
    //  * "bx tx-encode" for the "-i" argument needs one more element ":SATOSHIS" to specify the satoshis amount of the corresponding UTXO
    //    ..OR??
 
    //    Does this go into "bx input-sign"?
 
    //  *
 
    return 0;
}