import os
import sys
import unittest
import httpx

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app

class TestSubscriptionAPIs(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.transport = httpx.ASGITransport(app=app)
        self.client = httpx.AsyncClient(transport=self.transport, base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()

    async def test_health_check(self):
        response = await self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")

    async def test_full_subscription_lifecycle_api(self):
        # 1. Create a customer
        customer_payload = {
            "name": "Acme Innovations",
            "email": "finance@acme-innovations.io",
            "country": "US",
            "currency": "USD"
        }
        res_cust = await self.client.post("/api/v1/customers", json=customer_payload)
        self.assertEqual(res_cust.status_code, 201)
        customer_id = res_cust.json()["id"]

        # 2. Verify plans exist (pre-seeded)
        res_plans = await self.client.get("/api/v1/plans")
        self.assertEqual(res_plans.status_code, 200)
        plans = res_plans.json()
        self.assertGreater(len(plans), 0)
        starter_plan = next(p for p in plans if p["code"] == "starter")

        # 3. Subscribe customer to Starter Plan with 14-day trial
        sub_payload = {
            "customer_id": customer_id,
            "plan_id": starter_plan["id"],
            "start_with_trial": True
        }
        res_sub = await self.client.post("/api/v1/subscriptions", json=sub_payload)
        self.assertEqual(res_sub.status_code, 201)
        subscription = res_sub.json()
        self.assertEqual(subscription["status"], "trial")
        self.assertIsNotNone(subscription["trial_start"])
        self.assertIsNotNone(subscription["trial_end"])
        sub_id = subscription["id"]

        # 4. Cancel subscription
        cancel_payload = {
            "timing": "immediate",
            "reason": "Test trial cancellation"
        }
        res_cancel = await self.client.post(f"/api/v1/subscriptions/{sub_id}/cancel", json=cancel_payload)
        self.assertEqual(res_cancel.status_code, 200)
        self.assertEqual(res_cancel.json()["status"], "cancelled")

        # 5. Check audit logs
        res_audit = await self.client.get(f"/api/v1/audit-logs?customer_id={customer_id}")
        self.assertEqual(res_audit.status_code, 200)
        logs = res_audit.json()
        self.assertGreaterEqual(len(logs), 2)

if __name__ == "__main__":
    unittest.main()
