libbitcoin
$ gmake V=1 check
gmake  test/libbitcoin_test


gmake[1]: Entering directory '/home/phil/libbitcoin/src/libbitcoin'
/usr/local/bin/eg++ -DPACKAGE_NAME=\"libbitcoin\" -DPACKAGE_TARNAME=\"libbitcoin\" -DPACKAGE_VERSION=\"3.4.0\" -DPACKAGE_STRING=\"libbitcoin\ 3.4.0\" -DPACKAGE_BUGREPORT=\"eric@voskuil.org\" -DPACKAGE_URL=\"\" -DPACKAGE=\"libbitcoin\" -DVERSION=\"3.4.0\" -DSTDC_HEADERS=1 -DHAVE_SYS_TYPES_H=1 -DHAVE_SYS_STAT_H=1 -DHAVE_STDLIB_H=1 -DHAVE_STRING_H=1 -DHAVE_MEMORY_H=1 -DHAVE_STRINGS_H=1 -DHAVE_INTTYPES_H=1 -DHAVE_STDINT_H=1 -DHAVE_UNISTD_H=1 -D__EXTENSIONS__=1 -D_ALL_SOURCE=1 -D_GNU_SOURCE=1 -D_POSIX_PTHREAD_SEMANTICS=1 -D_TANDEM_SOURCE=1 -DHAVE_DLFCN_H=1 -DLT_OBJDIR=\".libs/\" -DHAVE_CXX11=1 -DBOOST_HAS_ICU=1 -DNDEBUG=1 -DBOOST_ALL_DYN_LINK=1 -DHAVE_BOOST=/\*\*/ -DHAVE_BOOST_CHRONO=/\*\*/ -DHAVE_BOOST_DATE_TIME=/\*\*/ -DHAVE_BOOST_FILESYSTEM=/\*\*/ -DHAVE_BOOST_IOSTREAMS=/\*\*/ -DHAVE_BOOST_LOCALE=/\*\*/ -DHAVE_BOOST_LOG=/\*\*/ -DHAVE_BOOST_PROGRAM_OPTIONS=/\*\*/ -DHAVE_BOOST_REGEX=/\*\*/ -DHAVE_BOOST_SYSTEM=/\*\*/ -DHAVE_BOOST_THREAD=/\*\*/ -DHAVE_BOOST_UNIT_TEST_FRAMEWORK=/\*\*/ -DHAVE_PTHREAD_PRIO_INHERIT=1 -I.  -I./include -DWITH_ICU -DWITH_PNG -DWITH_QRENCODE -I/home/phil/base/build/include  -I/usr/local/include -I/usr/local/include/libpng16 -I/usr/local/include -I/home/phil/libbitcoin/build/include   -std=c++11 -Og -g -fstack-protector-all -std=c++11 -Wno-deprecated-declarations -Wno-missing-braces -fvisibility-inlines-hidden -fno-var-tracking-assignments -MT test/utility/test_libbitcoin_test-data.o -MD -MP -MF test/utility/.deps/test_libbitcoin_test-data.Tpo -c -o test/utility/test_libbitcoin_test-data.o `test -f 'test/utility/data.cpp' || echo './'`test/utility/data.cpp
test/utility/data.cpp: In member function 'void data_tests::data__splice_two__two_bytes_each__expected::test_method()':
test/utility/data.cpp:253:27: error: reference to 'splice' is ambiguous
     const auto combined = splice(left, right);
                           ^
In file included from /home/phil/base/build/include/boost/asio/detail/socket_types.hpp:77:0,
                 from /home/phil/base/build/include/boost/asio/detail/impl/pipe_select_interrupter.ipp:31,
                 from /home/phil/base/build/include/boost/asio/detail/pipe_select_interrupter.hpp:82,
                 from /home/phil/base/build/include/boost/asio/detail/select_interrupter.hpp:27,
                 from /home/phil/base/build/include/boost/asio/detail/kqueue_reactor.hpp:32,
                 from /home/phil/base/build/include/boost/asio/detail/reactor.hpp:23,
                 from /home/phil/base/build/include/boost/asio/detail/impl/scheduler.ipp:23,
                 from /home/phil/base/build/include/boost/asio/detail/scheduler.hpp:212,
                 from /home/phil/base/build/include/boost/asio/system_context.hpp:19,
                 from /home/phil/base/build/include/boost/asio/impl/system_executor.hpp:22,
                 from /home/phil/base/build/include/boost/asio/system_executor.hpp:129,
                 from /home/phil/base/build/include/boost/asio/associated_executor.hpp:21,
                 from /home/phil/base/build/include/boost/asio.hpp:21,
                 from ./include/bitcoin/bitcoin/utility/asio.hpp:24,
                 from ./include/bitcoin/bitcoin/chain/block.hpp:35,
                 from ./include/bitcoin/bitcoin.hpp:24,
                 from test/utility/data.cpp:24:
/usr/include/sys/socket.h:138:8: note: candidates are: struct splice
 struct splice {
        ^
In file included from ./include/bitcoin/bitcoin/utility/data.hpp:156:0,
                 from ./include/bitcoin/bitcoin/math/hash.hpp:29,
                 from ./include/bitcoin/bitcoin/formats/base_16.hpp:24,
                 from ./include/bitcoin/bitcoin/config/checkpoint.hpp:27,
                 from ./include/bitcoin/bitcoin/constants.hpp:25,
                 from ./include/bitcoin/bitcoin.hpp:19,
                 from test/utility/data.cpp:24:
./include/bitcoin/bitcoin/impl/utility/data.ipp:100:35: note:                 template<long unsigned int Left, long unsigned int Middle, long unsigned int Right> libbitcoin::byte_array<((Left + Middle) + Right)> libbitcoin::splice(const std byte_array<Left + Middle + Right> splice(const std::array<uint8_t, Left>& left,
                                   ^
./include/bitcoin/bitcoin/impl/utility/data.ipp:91:26: note:                 template<long unsigned int Left, long unsigned int Right> libbitcoin::byte_array<(Left + Right)> libbitcoin::splice(const std::array<unsigned char, Size>&, const std::array<unsigned char, Right>&)
 byte_array<Left + Right> splice(const std::array<uint8_t, Left>& left,
                          ^
test/utility/data.cpp: In member function 'void data_tests::data__splice_three__one_two_three_bytes__expected::test_method()':
test/utility/data.cpp:278:27: error: reference to 'splice' is ambiguous
     const auto combined = splice(left, middle, right);
                           ^
In file included from /home/phil/base/build/include/boost/asio/detail/socket_types.hpp:77:0,
                 from /home/phil/base/build/include/boost/asio/detail/impl/pipe_select_interrupter.ipp:31,
                 from /home/phil/base/build/include/boost/asio/detail/pipe_select_interrupter.hpp:82,
                 from /home/phil/base/build/include/boost/asio/detail/select_interrupter.hpp:27,
                 from /home/phil/base/build/include/boost/asio/detail/kqueue_reactor.hpp:32,
                 from /home/phil/base/build/include/boost/asio/detail/reactor.hpp:23,
                 from /home/phil/base/build/include/boost/asio/detail/impl/scheduler.ipp:23,
                 from /home/phil/base/build/include/boost/asio/detail/scheduler.hpp:212,
                 from /home/phil/base/build/include/boost/asio/system_context.hpp:19,
                 from /home/phil/base/build/include/boost/asio/impl/system_executor.hpp:22,
                 from /home/phil/base/build/include/boost/asio/system_executor.hpp:129,
                 from /home/phil/base/build/include/boost/asio/associated_executor.hpp:21,
                 from /home/phil/base/build/include/boost/asio.hpp:21,
                 from ./include/bitcoin/bitcoin/utility/asio.hpp:24,
                 from ./include/bitcoin/bitcoin/chain/block.hpp:35,
                 from ./include/bitcoin/bitcoin.hpp:24,
                 from test/utility/data.cpp:24:
/usr/include/sys/socket.h:138:8: note: candidates are: struct splice
 struct splice {
        ^
In file included from ./include/bitcoin/bitcoin/utility/data.hpp:156:0,
                 from ./include/bitcoin/bitcoin/math/hash.hpp:29,
                 from ./include/bitcoin/bitcoin/formats/base_16.hpp:24,
                 from ./include/bitcoin/bitcoin/config/checkpoint.hpp:27,
                 from ./include/bitcoin/bitcoin/constants.hpp:25,
                 from ./include/bitcoin/bitcoin.hpp:19,
                 from test/utility/data.cpp:24:
./include/bitcoin/bitcoin/impl/utility/data.ipp:100:35: note:                 template<long unsigned int Left, long unsigned int Middle, long unsigned int Right> libbitcoin::byte_array<((Left + Middle) + Right)> libbitcoin::splice(const std::array<unsigned char, Size>&, const std::array<unsigned char, Right>&, const std::array<unsigned char, Size>&)
 byte_array<Left + Middle + Right> splice(const std::array<uint8_t, Left>& left,
                                   ^
./include/bitcoin/bitcoin/impl/utility/data.ipp:91:26: note:                 template<long unsigned int Left, long unsigned int Right> libbitcoin::byte_array<(Left + Right)> libbitcoin::splice(const std::array<unsigned char, Size>&, const std::array<unsigned char, Right>&)
 byte_array<Left + Right> splice(const std::array<uint8_t, Left>& left,
                          ^
gmake[1]: *** [Makefile:4951: test/utility/test_libbitcoin_test-data.o] Error 1
gmake[1]: Leaving directory '/home/phil/libbitcoin/src/libbitcoin'
gmake: *** [Makefile:6102: check-am] Error 2
