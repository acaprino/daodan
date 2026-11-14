class Order < ApplicationRecord
  after_create_commit { ReceiptJob.perform_later(id) }
end
