require "rails_helper"

RSpec.describe Order, type: :model do
  it "enqueues a receipt after create" do
    expect { Order.create! }.to have_enqueued_job(ReceiptJob)
  end
end
