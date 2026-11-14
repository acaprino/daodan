.PHONY: gen serve

gen:
	cd frontend && npm run gen:api

serve:
	cd backend && uvicorn orders_backend.main:app --reload
