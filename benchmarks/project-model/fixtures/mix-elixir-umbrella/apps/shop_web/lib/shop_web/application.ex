defmodule ShopWeb.Application do
  @moduledoc false
  use Application

  @impl true
  def start(_type, _args) do
    :telemetry.execute([:shop_web, :start], %{port: Application.get_env(:shop_web, :port)})
    Supervisor.start_link([], strategy: :one_for_one, name: ShopWeb.Supervisor)
  end
end
