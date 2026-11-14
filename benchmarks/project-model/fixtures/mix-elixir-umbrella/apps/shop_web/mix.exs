defmodule ShopWeb.MixProject do
  use Mix.Project

  def project do
    [
      app: :shop_web,
      version: "0.1.0",
      build_path: "../../_build",
      config_path: "../../config/config.exs",
      deps_path: "../../deps",
      lockfile: "../../mix.lock",
      elixir: "~> 1.17",
      start_permanent: Mix.env() == :prod,
      deps: deps()
    ]
  end

  def application do
    [
      mod: {ShopWeb.Application, []},
      extra_applications: [:logger]
    ]
  end

  defp deps do
    [
      {:shop_core, in_umbrella: true},
      {:telemetry, "~> 1.3"}
    ]
  end
end
