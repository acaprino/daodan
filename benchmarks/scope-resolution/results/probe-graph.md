# Probe graph (Task 2) — create_run: esistente: run already exists; resume the exact run or choose another run_id

I path sono repo-relativi (prefix `benchmarks/scope-resolution/app/`).

## benchmarks/scope-resolution/app/packages/orders/service.py (hops=1)

```json
[
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/api.py::function@34:0",
  "parts": [
   "OrderService"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/service.py::class@18:0"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@19:4",
  "parts": [
   "setattr"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@19:4",
  "parts": [],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@23:4",
  "parts": [
   "inventory",
   "reserve_stock"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/inventory.py::function@14:0"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@23:4",
  "parts": [
   "pricing",
   "compute_total"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/pricing.py::function@17:0"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@23:4",
  "parts": [
   "self",
   "_pipeline",
   "step"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@23:4",
  "parts": [
   "ledger",
   "record"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/ledger.py::function@13:0"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@23:4",
  "parts": [
   "notifications",
   "send_via"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/notifications.py::function@8:0"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@23:4",
  "parts": [
   "order",
   "get"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@32:4",
  "parts": [
   "ledger",
   "record_refund"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/ledger.py::function@25:0"
 }
]
```

## benchmarks/scope-resolution/app/packages/orders/api.py (hops=1)

```json
[
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/api.py::function@25:4",
  "parts": [
   "handler"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/api.py::function@29:4",
  "parts": [
   "self",
   "_invoke"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/api.py::function@25:4"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/api.py::function@34:0",
  "parts": [
   "OrderService"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/service.py::class@18:0"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/api.py::function@34:0",
  "parts": [
   "on_event"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/api.py::function@13:0"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/api.py::function@34:0",
  "parts": [
   "on_event"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/api.py::function@13:0"
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/api.py::function@34:0",
  "parts": [
   "Dispatcher"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/api.py::class@19:0"
 }
]
```

## benchmarks/scope-resolution/app/packages/payments/gateway.py (hops=1)

```json
[
 {
  "caller": "benchmarks/scope-resolution/app/packages/payments/gateway.py::function@8:0",
  "parts": [
   "order",
   "get"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/payments/gateway.py::function@13:0",
  "parts": [
   "order",
   "get"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/payments/gateway.py::function@24:0",
  "parts": [
   "handler"
  ],
  "resolution": "unresolved",
  "target": null
 }
]
```

## benchmarks/scope-resolution/app/packages/orders/notifications.py (hops=1)

```json
[
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/notifications.py::function@8:0",
  "parts": [
   "globals"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/notifications.py::function@8:0",
  "parts": [
   "sender"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/notifications.py::function@15:0",
  "parts": [
   "order",
   "get"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/notifications.py::function@20:0",
  "parts": [
   "order",
   "get"
  ],
  "resolution": "unresolved",
  "target": null
 },
 {
  "caller": "benchmarks/scope-resolution/app/packages/orders/service.py::function@23:4",
  "parts": [
   "notifications",
   "send_via"
  ],
  "resolution": "resolved",
  "target": "benchmarks/scope-resolution/app/packages/orders/notifications.py::function@8:0"
 }
]
```

## modules(query='shipping')

```json
{
 "status": "resolved",
 "reason": "one confirmed module matches the name",
 "names": [
  "shipping"
 ],
 "files": [
  "benchmarks/scope-resolution/app/packages/shipping/__init__.py",
  "benchmarks/scope-resolution/app/packages/shipping/rates.py"
 ]
}
```
