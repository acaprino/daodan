class CheckoutService {
  constructor(store) { this.store = store; }
  create(plan) { return this.store.save({ plan }); }
}
class MemoryStore {
  save(row) { return row; }
}
module.exports = { CheckoutService, MemoryStore };
