Rails.application.routes.draw do
  resources :orders, only: [:index]
end
