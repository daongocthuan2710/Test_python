import io
import pytest
import json
from app import app, in_memory_data

@pytest.fixture
def client():
    """
    This fixture sets up a test client for our Flask app.
    It also ensures that TESTING is enabled.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_upload_csv_success(client):
    global in_memory_data
    """
    Test uploading a valid CSV file and check if the response is successful.
    """

    sample_csv = b"date,region,price,quantity\n2024-01-01,USA,100,2\n2024-01-02,Canada,50,3"
    
    data = {
        'file': (io.BytesIO(sample_csv), 'test.csv')
    }
    response = client.post('/upload', data=data, content_type='multipart/form-data')
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    json_data = response.get_json()
    assert json_data['message'] == 'File uploaded and stored in memory successfully.'
    assert 'num_rows' in json_data
    assert json_data['num_rows'] == 2

def test_sales_no_data(client):
    global in_memory_data
    """
    Test calling /sales before any CSV is uploaded.
    Should return error message.
    """
    response = client.get('/sales')
    assert response.status_code == 400
    json_data = response.get_json()
    assert json_data['error'] == 'No CSV data in memory. Please upload first.'

def test_sales_filtering(client):
    global in_memory_data
    """
    Test uploading a CSV, then calling /sales with filters.
    """

    sample_csv = b"date,region,price,quantity\n" \
                 b"2024-01-01,USA,100,2\n" \
                 b"2024-01-05,USA,200,1\n" \
                 b"2024-01-10,Canada,50,4\n"
    
    data = {
        'file': (io.BytesIO(sample_csv), 'test.csv')
    }
    upload_resp = client.post('/upload', data=data, content_type='multipart/form-data')
    assert upload_resp.status_code == 200

    resp = client.get('/sales')
    assert resp.status_code == 200
    json_data = resp.get_json()

    assert 'data' in json_data
    assert 'total_sales' in json_data
    assert 'average_sales' in json_data
    assert 'count_transactions' in json_data

    assert len(json_data['data']) == 3
    assert json_data['total_records'] == 3
    assert json_data['total_sales'] == 600

    resp_usa = client.get('/sales?region=USA')
    json_usa = resp_usa.get_json()

    assert len(json_usa['data']) == 2
    assert json_usa['total_sales'] == 400

    resp_date = client.get('/sales?start_date=2024-01-02')
    json_date = resp_date.get_json()
    assert len(json_date['data']) == 2
    assert json_date['total_sales'] == 400

def test_sales_pagination(client):
    global in_memory_data
    """
    Test pagination logic. We'll upload 5 rows and request a limit=2.
    """
    sample_csv = b"date,region,price,quantity\n" \
                 b"2024-01-01,USA,100,2\n" \
                 b"2024-01-02,USA,50,3\n" \
                 b"2024-01-03,Canada,200,1\n" \
                 b"2024-01-04,USA,150,2\n" \
                 b"2024-01-05,USA,120,1\n"
    data = {
        'file': (io.BytesIO(sample_csv), 'test.csv')
    }
    upload_resp = client.post('/upload', data=data, content_type='multipart/form-data')
    assert upload_resp.status_code == 200

    resp_p1 = client.get('/sales?page=1&limit=2')
    assert resp_p1.status_code == 200
    json_p1 = resp_p1.get_json()
    assert len(json_p1['data']) == 2
    assert json_p1['page'] == 1
    assert json_p1['limit'] == 2
    assert json_p1['total_records'] == 5
    assert json_p1['total_pages'] == 3

    resp_p2 = client.get('/sales?page=2&limit=2')
    json_p2 = resp_p2.get_json()
    assert len(json_p2['data']) == 2
    assert json_p2['page'] == 2

    resp_p3 = client.get('/sales?page=3&limit=2')
    json_p3 = resp_p3.get_json()
    assert len(json_p3['data']) == 1
    assert json_p3['page'] == 3
