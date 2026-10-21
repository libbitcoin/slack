wait just FYR, some feedback from some C++ coders on https://github.com/libbitcoin/libbitcoin/blob/version3/include/bitcoin/bitcoin/utility/atomic.hpp , they think it could be written in a better way


1)
"The use of std forward does the right thing but is not idiomatic. It should use std::move"


2)
<SlashLife> atomic(Type&& instance): instance_(std::forward<Type>(instance)) // <-- Better question: What's the point of the std::forward?
<SlashLife> imo: This (code) is BS.
<SlashLife> The use of std::decay in it is, and a bunch of the other templating stuff as well.
<Oxyd> That forward almost makes sense. Shame that Type isn't a forwarding reference.
<Oxyd> It's like someone read a C++ tutorial and almost understood it.
<SlashLife> Oxyd: It doesn't make sense the way it is used there.
<SlashLife> Type is determined by the struct, not by the ctor.
<SlashLife> Instead they should restrict the Type they take to non-refs (and potentially to non-cv as well)
<SlashLife> Jmabsd: That last line was for you again.
<SlashLife> Where they go wrong: They didn't think about what kind of types they'd want to allow, ending up with contradicting usage concepts, therefore incorrecly applying template programming concepts.
<Oxyd> Well, one major thing is that it always uses a mutex. The point of std::atomic is to get a lock-free access (at least sometimes).
<SlashLife> That std::forward should instead have been an std::move; almost all uses of Type within that struct should be replaced with decayed_type
<SlashLife> Unless of course Type is a reference.
<SlashLife> But then you have an atomic<int&>, which doesn't even store a reference to int, but is just the same as an int.
<SlashLife> Except that it won't have move operations, but instead copy operations for both const and non-const refs.
<SlashLife> So being able to pass T& to it makes you believe it could store a reference. But it doesn't. Instead it disables move semantics if T has them.
<SlashLife> So if you pass T&, it is actively misleading in what it does.
<SlashLife> Now you could say that maybe this is not intended to pass T&, and they just didn't add code to catch that - sure, that could be. But they did add a bunch of other code (including those std::forward) which specifically suggest graceful handling of reference types.
<SlashLife> If your T is not a T&, then std::forward<T> means std::move
