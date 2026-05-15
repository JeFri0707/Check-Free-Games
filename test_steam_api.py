import requests, sys, urllib3
urllib3.disable_warnings()
h = {'User-Agent': 'Mozilla/5.0'}

# Test different formats
test_ids = '730,440,570'
r1 = requests.get('https://store.steampowered.com/api/appdetails', params={'appids': test_ids, 'cc': 'us'}, headers=h, timeout=10)
sys.stdout.buffer.write(f'Comma-separated: {r1.status_code}\n'.encode())

# Multiple appids params
r2 = requests.get('https://store.steampowered.com/api/appdetails?appids=730&appids=440&appids=570&cc=us', headers=h, timeout=10)
sys.stdout.buffer.write(f'Multi-param: {r2.status_code}\n'.encode())

# Test with a larger set (50 appids)
ids_50 = ','.join([str(x) for x in range(730, 780)])
r3 = requests.get('https://store.steampowered.com/api/appdetails', params={'appids': ids_50, 'cc': 'us'}, headers=h, timeout=10)
sys.stdout.buffer.write(f'50 comma-separated: {r3.status_code}\n'.encode())

# Test real appids from the error log
real_ids = '10076,1174180,1229490,1243500,1641346,1663850,2215200,2479810,2483190,2590410,2629230,264710,3017860,3124540,3263540,3373600,3404260,3486960,3521220,3554150,3595320,3602030,3826060,3922090,3950510,3989810,4117320,413150,4182000,4341480,4359120,4380000,4391540,4396370,4506500,4512000,4519280,4539950,4541390,4568150,4591700,4591720,4613260,4628500,4629780,4645490,4651320,4655400,4662430,4663010'
r4 = requests.get('https://store.steampowered.com/api/appdetails', params={'appids': real_ids, 'cc': 'us', 'l': 'english'}, headers=h, timeout=10)
sys.stdout.buffer.write(f'Real IDs comma-separated: {r4.status_code}\n'.encode())
if r4.status_code == 200:
    data = r4.json()
    sys.stdout.buffer.write(f'Keys in response: {len(data)}\n'.encode())
