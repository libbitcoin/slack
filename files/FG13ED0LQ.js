case script_pattern::sign_key_hash:
        {
            return
            {
                { ec_public{ script[1].data() }, p2kh_version },
                { bitcoin_short_hash(script.back().data()), p2sh_version }
            };
        }