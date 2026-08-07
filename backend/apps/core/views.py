"""Health and readiness endpoints."""

from django.conf import settings
from django.db import connection
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request):
        return Response({"status": "ok", "service": "codescope-api"})


class ReadyView(APIView):
    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request):
        checks: dict[str, str] = {}
        overall = True

        try:
            connection.ensure_connection()
            checks["postgres"] = "ok"
        except Exception as exc:  # noqa: BLE001
            checks["postgres"] = f"error: {exc}"
            overall = False

        try:
            import redis

            client = redis.from_url(settings.REDIS_URL)
            client.ping()
            checks["redis"] = "ok"
        except Exception as exc:  # noqa: BLE001
            checks["redis"] = f"error: {exc}"
            # Redis optional for basic API in local SQLite mode
            if not settings.DEBUG:
                overall = False

        if settings.NEO4J_ENABLED:
            try:
                from neo4j import GraphDatabase

                driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
                )
                driver.verify_connectivity()
                driver.close()
                checks["neo4j"] = "ok"
            except Exception as exc:  # noqa: BLE001
                checks["neo4j"] = f"error: {exc}"
                if not settings.DEBUG:
                    overall = False
        else:
            checks["neo4j"] = "disabled"

        code = status.HTTP_200_OK if overall else status.HTTP_503_SERVICE_UNAVAILABLE
        return Response({"status": "ready" if overall else "degraded", "checks": checks}, status=code)
