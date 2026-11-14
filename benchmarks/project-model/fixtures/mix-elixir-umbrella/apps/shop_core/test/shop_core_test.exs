defmodule ShopCoreTest do
  use ExUnit.Case

  test "encodes an order" do
    assert ShopCore.encode_order(%{id: 1}) == ~s({"id":1})
  end
end
