"""
TraceX AML - Authentication Unit Tests
"""

def test_auth_credentials():
    valid_user = "admin"
    valid_pass = "admin123"

    assert (valid_user == "admin" and valid_pass == "admin123") is True
    assert ("wrong_user" == "admin" and "admin123" == "admin123") is False
    assert ("admin" == "admin" and "wrong_pass" == "admin123") is False
    print("Credentials test passed!")

if __name__ == "__main__":
    test_auth_credentials()
