defmodule ShopCore do
  @moduledoc "Orders encoded as JSON."

  def encode_order(order), do: Jason.encode!(order)
end
