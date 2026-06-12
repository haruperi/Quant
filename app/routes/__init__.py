"""API Route Routers subpackage.

Routes should do three things:
- Validate request
- Call service
- Return response

Nothing else.

Group related endpoints here, not in main.py:

- auth.py → /api/auth/*
- users.py → /api/users/*
- trading.py → /api/trading/*
- research.py → /api/research/*
- strategy.py → /api/strategy/*
- signal.py → /api/signal/*

Each file exports an APIRouter instance.
"""
