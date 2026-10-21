void block_chain::fetch_history(const short_hash& address_hash, size_t limit,
    size_t from_height, history_fetch_handler handler) const
{
    if (stopped())
    {
        handler(error::service_stopped, {});
        return;
    }

    // Cannot know size without reading all, so dynamically allocate.
    chain::payment_record::list payments;
    size_t count = 0;

    // Result set is ordered most recent tx first (reverse point order in tx).
    for (auto payment: database_.addresses().get(address_hash))
    {
        if (count++ == limit)
            break;

        const auto tx = database_.transactions().get(payment.link());
        const auto height = tx.height();

        if (height < from_height)
            break;

        // Copy of each payment record above so can be modified here.
        payment.set_height(height);
        payment.set_hash(tx.hash());
        payments.push_back(payment);
    }

    handler(error::success, std::move(payments));
}