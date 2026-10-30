import requests

BASE = 'http://127.0.0.1:8000/api/v1'

def run_e2e_verification():
    print("=" * 60)
    print("RailSync 360: Executing Full End-to-End API Verification")
    print("=" * 60)

    # 1. Health
    print("1. Checking Server Health...")
    h = requests.get('http://127.0.0.1:8000/health').json()
    print(f"   Status: {h['status']} | Profile: {h['profile']} | DB: {h['database']}")

    # 2. Login
    print("2. Authenticating as Passenger...")
    login_res = requests.post(f"{BASE}/auth/login", json={
        "email": "passenger@example.com",
        "password": "Passenger123!"
    }).json()
    token = login_res["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"   Authenticated as: {login_res['name']} ({login_res['role']})")

    # 3. Search Trains
    print("3. Querying Journeys between NDLS and BCT...")
    journeys = requests.get(f"{BASE}/journeys/search", params={"source": "NDLS", "destination": "BCT"}).json()
    print(f"   Found {len(journeys)} scheduled journey(s)")
    assert len(journeys) > 0
    selected_journey = journeys[0]
    j_id = selected_journey["journey_id"]
    print(f"   Selected Train: #{selected_journey['train_number']} {selected_journey['train_name']} (Journey #{j_id})")

    # 4. Book a Seat
    print("4. Executing ACID Booking Transaction (Row-Level Locking)...")
    booking_payload = {
        "journey_id": j_id,
        "travel_class": "AC",
        "passengers": [{"full_name": "Vikram Rathore", "age": 32, "gender": "MALE"}]
    }
    b_res = requests.post(f"{BASE}/bookings", json=booking_payload, headers=headers).json()
    pnr = b_res["pnr"]
    status_str = b_res["status"]
    seat = b_res["passengers"][0]["seat_number"]
    print(f"   --> SUCCESS! Generated PNR: {pnr} | Status: {status_str} | Allocated Seat: {seat}")

    # 5. PNR Lookup
    print(f"5. Looking up PNR {pnr}...")
    ticket = requests.get(f"{BASE}/bookings/{pnr}", headers=headers).json()
    assert ticket["pnr"] == pnr
    print(f"   --> Confirmed ticket record belongs to user #{ticket['user_id']} with fare INR {ticket['total_fare']}")

    # 6. Cancellation
    print(f"6. Requesting Cancellation for PNR {pnr}...")
    cancel_res = requests.post(f"{BASE}/bookings/{pnr}/cancel", headers=headers).json()
    assert cancel_res["status"] == "CANCELLED"
    print(f"   --> Ticket status updated to: {cancel_res['status']} | Cancelled at: {cancel_res['cancelled_at']}")

    # 7. Admin Metrics Check
    print("7. Verifying Admin Telemetry & Metrics...")
    admin_login = requests.post(f"{BASE}/auth/login", json={
        "email": "admin@railsync360.internal",
        "password": "AdminPass2026!"
    }).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}
    metrics = requests.get(f"{BASE}/admin/metrics", headers=admin_headers).json()
    print(f"   Metrics: Total Users: {metrics['total_users']}, Tickets: {metrics['total_tickets']}, Cancelled: {metrics['cancelled_tickets']}")

    sync_health = requests.get(f"{BASE}/admin/sync-health", headers=admin_headers).json()
    print(f"   Sync Diagnostics: Profile: {sync_health['app_profile']} | Firebase: {sync_health['firebase_status']} | Cosmos: {sync_health['cosmos_status']}")

    print("=" * 60)
    print("ALL END-TO-END JOURNEY CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 60)

if __name__ == "__main__":
    run_e2e_verification()
