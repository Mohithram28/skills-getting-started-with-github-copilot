"""
Tests for the High School Management System API
"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_index(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint"""

    def test_get_activities_returns_list(self, client):
        """Test that /activities returns a list of activities"""
        response = client.get("/activities")
        assert response.status_code == 200

        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0

    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()

        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_has_basketball(self, client):
        """Test that Basketball activity is in the list"""
        response = client.get("/activities")
        activities = response.json()
        assert "Basketball" in activities
        assert activities["Basketball"]["max_participants"] == 15


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""

    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]

    def test_signup_adds_participant_to_list(self, client):
        """Test that signup actually adds the participant to the list"""
        # Signup a new student
        response = client.post(
            "/activities/Tennis Club/signup",
            params={"email": "new_tennis@mergington.edu"}
        )
        assert response.status_code == 200

        # Verify the student is now in the participants list
        activities = client.get("/activities").json()
        assert "new_tennis@mergington.edu" in activities["Tennis Club"]["participants"]

    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up with an already registered email fails"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "alex@mergington.edu"}  # Already registered
        )
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signing up for a non-existent activity fails"""
        response = client.post(
            "/activities/NonExistentActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity"""
        # First signup
        client.post(
            "/activities/Drama Club/signup",
            params={"email": "drama_student@mergington.edu"}
        )

        # Then unregister
        response = client.delete(
            "/activities/Drama Club/unregister",
            params={"email": "drama_student@mergington.edu"}
        )
        assert response.status_code == 200
        result = response.json()
        assert "Unregistered" in result["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "unregister_test@mergington.edu"

        # Signup
        client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )

        # Verify signup
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]

        # Unregister
        client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )

        # Verify removal
        activities = client.get("/activities").json()
        assert email not in activities["Chess Club"]["participants"]

    def test_unregister_nonexistent_email_fails(self, client):
        """Test that unregistering a non-existent email fails"""
        response = client.delete(
            "/activities/Programming Class/unregister",
            params={"email": "nonexistent@mergington.edu"}
        )
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregistering from a non-existent activity fails"""
        response = client.delete(
            "/activities/NonExistentActivity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        result = response.json()
        assert "not found" in result["detail"]


class TestActivityIntegration:
    """Integration tests for signup and unregister workflows"""

    def test_signup_and_unregister_workflow(self, client):
        """Test the full workflow of signing up and then unregistering"""
        email = "workflow_test@mergington.edu"
        activity = "Gym Class"

        # Get initial participants count
        initial_activities = client.get("/activities").json()
        initial_count = len(initial_activities[activity]["participants"])

        # Signup
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200

        # Verify participant was added
        activities = client.get("/activities").json()
        assert len(activities[activity]["participants"]) == initial_count + 1
        assert email in activities[activity]["participants"]

        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200

        # Verify participant was removed
        activities = client.get("/activities").json()
        assert len(activities[activity]["participants"]) == initial_count
        assert email not in activities[activity]["participants"]

    def test_multiple_signups_for_different_activities(self, client):
        """Test signing up for multiple activities with the same email"""
        email = "multi_study@mergington.edu"

        # Sign up for multiple activities
        activities_to_join = ["Art Studio", "Science Club"]

        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Verify the student is in all activities
        activities = client.get("/activities").json()
        for activity in activities_to_join:
            assert email in activities[activity]["participants"]
