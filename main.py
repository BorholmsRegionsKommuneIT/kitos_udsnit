import collections.abc
import json
import os
from pathlib import Path

import pandas as pd
import requests
from dotenv import load_dotenv
from flatten_json import flatten

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", 100)
pd.set_option("display.expand_frame_repr", False)


# ------------------------------ read .env file ------------------------------ #
load_dotenv()
PAM_PATH = Path(os.getenv("PAM_PATH"))
uuid_kommune = os.getenv("kommune_uuid")

with open(Path(f"{PAM_PATH}/kitos/kitos.json"), "r") as file:
    cred = json.load(file)

email = cred["kitos"].get("username")
password = cred["kitos"].get("password")

# --------------------------------- Get token -------------------------------- #
url_authorize = "https://kitos.dk/api/authorize/gettoken/"
payload = {"email": email, "password": password}
resp = requests.post(url_authorize, json=payload)

# Get token
resp.raise_for_status()
data = resp.json()
token = data["response"]["token"]

# --------------------------------- Base url --------------------------------- #
base_url = "https://kitos.dk/api/v2"


# --------------------------------- Functions -------------------------------- #
def get_data_from_kitos_api(endpoint, params=None):
    """
    Fetch data from Kitos API endpoint with pagination support.
    """
    page_size = 100
    page = 0
    has_more_data = True
    all_data = []

    while has_more_data:
        # Construct URL for current page
        url = f"{base_url}{endpoint}?page={page}&pageSize={page_size}"
        if params:
            url += "&" + "&".join([f"{key}={value}" for key, value in params.items()])

        # Make the request
        response = requests.get(url, headers={"Authorization": f"Bearer {token}"})
        response.raise_for_status()

        # Get the current page of data
        current_page_data = response.json()

        # If we received data, add it to our collection
        if current_page_data and len(current_page_data) > 0:
            all_data.extend(current_page_data)
            # Move to the next page
            page += 1
        else:
            # No more data, exit the loop
            has_more_data = False

    return all_data


def get_system_administrators(roles_data):
    """
    Parse user and role information (either as JSON string or Python list)
    and return a list of names for users with the 'Systemadministrator' role.

    Args:
        roles_data: Either a JSON string or Python list with user and role information

    Returns:
        list: Names of users with the 'Systemadministrator' role
    """
    # Check if input is already a Python list/dict or if it needs parsing
    if isinstance(roles_data, str):
        try:
            data = json.loads(roles_data)
        except json.JSONDecodeError:
            return []  # Return empty list if invalid JSON
    else:
        # Input is already a Python list/dict
        data = roles_data

    # Define the target role name
    target_role = "Systemadministrator"

    # Filter users with the target role
    system_administrators = []
    for item in data:
        if item["role"]["name"] == target_role:
            system_administrators.append(item["user"]["name"])

    return system_administrators


def get_external_references_dict(external_references):
    """
    Parse external references data and return a dictionary mapping titles to URLs.

    Args:
        external_references: List of dictionaries containing external reference information

    Returns:
        dict: Dictionary mapping titles to URLs (skipping entries with None URL)
    """
    # Check if input is already a Python list/dict or if it needs parsing
    if isinstance(external_references, str):
        try:
            data = json.loads(external_references)
        except json.JSONDecodeError:
            return {}  # Return empty dict if invalid JSON
    else:
        # Input is already a Python list/dict
        data = external_references

    # Create dictionary mapping titles to URLs, skipping None URLs
    title_url_dict = {}
    for item in data:
        title = item.get("title")
        url = item.get("url")

        # Only add entries with valid URLs
        if title and url is not None:
            if isinstance(url, str):
                url = url.strip()
            title_url_dict[title] = url

    return title_url_dict


# ---------------------------------------------------------------------------- #
#                               IT System (navn)                               #
# ---------------------------------------------------------------------------- #

endpoint = "/it-systems"
params = {"organizationUuid": uuid_kommune}
all_it_systems = get_data_from_kitos_api(endpoint, params)


df_all_it_systems = pd.DataFrame(all_it_systems)

df_all_it_systems_subset = df_all_it_systems[["uuid", "name", "description"]].copy()

# * uuid_system,  name, description
df_all_it_systems_partial = df_all_it_systems_subset.rename(columns={"uuid": "uuid_system"})

df_all_it_systems_partial["uuid_system"]

endpoint = "/it-system-usages"
params = {"organizationUuid": uuid_kommune}
all_it_system_usages = get_data_from_kitos_api(endpoint, params)


df_it_system_usages = pd.DataFrame(all_it_system_usages)

df_it_system_usages_subset = df_it_system_usages[
    [
        "uuid",
        "systemContext",
        "general",
        "organizationUsage",
        "roles",
        "externalReferences",
    ]
].copy()


# rename df_it_system_usages_valid["uuid"] to "uuid_usage"
df_it_system_usages_subset = df_it_system_usages_subset.rename(columns={"uuid": "uuid_usage"}).copy()

# Filter to keep only rows where general.validity.valid is True
df_it_system_usages_valid = df_it_system_usages_subset[
    df_it_system_usages_subset["general"].apply(lambda x: x["validity"]["valid"])
].copy()


# replace roles with system admins
df_it_system_usages_valid.loc[:, "system_admins"] = df_it_system_usages_valid["roles"].apply(get_system_administrators)

# Get external references (referencer)
df_it_system_usages_valid.loc[:, "title_url_dict"] = df_it_system_usages_valid["externalReferences"].apply(
    get_external_references_dict
)


# drop roles
df_it_system_usages_valid = df_it_system_usages_valid.drop(columns=["roles"]).copy()

# from df_it_system_usages_valid select columns uuid_usage, system_admins, title_url_dict
df_it_system_usages_valid = df_it_system_usages_valid[["uuid_usage", "system_admins", "title_url_dict"]].copy()

# flatten cols ["uuid", "systemContext", "organizationUsage"]
# flat = pd.json_normalize(df_it_system_usages_valid.to_dict(orient="records"), sep=".")
# test = flatten(all_it_system_usages[0])

flat_usages = [flatten(d) for d in all_it_system_usages]

df_flat_usages = pd.DataFrame(flat_usages)

df_flat_usages_valid = df_flat_usages[df_flat_usages["general_validity_valid"]]

df_flat_usages_valid.shape[0] == len(df_it_system_usages_valid)


# rename uuid to uuid_usage
df_flat_usages_valid = df_flat_usages_valid.rename(columns={"uuid": "uuid_usage"})

want = df_flat_usages_valid[
    [
        "uuid_usage",
        "systemContext_uuid",
        "systemContext_name",
        "general_localCallName",
        "organizationUsage_responsibleOrganizationUnit_name",
        "organizationUsage_usingOrganizationUnits_1_name",
    ]
].rename(
    columns={
        "uuid_usage": "uuid_usage",
        "systemContext_uuid": "uuid_system",
        "systemContext_name": "system_name",
        "general_localCallName": "system_name_local",
        "organizationUsage_responsibleOrganizationUnit_name": "ansvarlig_organisationsenhed",
        "organizationUsage_usingOrganizationUnits_1_name": "relevante_organisationsenheder",
    }
)


# * "uuid_usage",  # want["uuid_usage"]
# * "uuid_system",  # want["systemContext_uuid"]
# * "system_name",  # want["system_name"]
# * "system_name_local",  # want["system_name_local"]
# * "ansvarlig_organisationsenhed",  # want["ansvarlig_organisationsenhed"]
# * "relevante_organisationsenheder",  # want["relevante_organisationsenheder"]
# * "system_admins",  # df_it_system_usages_valid["system_admins"]
# * "title_url_dict",  # df_it_system_usages_valid["title_url_dict"]


df_it_system_usages_partial = pd.merge(df_it_system_usages_valid, want, on="uuid_usage", how="left")

# ---------------------------------------------------------------------------- #
#                       Leverandør fra kontrakt endpoint                       #
# ---------------------------------------------------------------------------- #

endpoint = "/it-contracts"
params = {"organizationUuid": uuid_kommune}
all_it_contracts = get_data_from_kitos_api(endpoint, params)


# Inspect it_systems
df_all_it_contracts = pd.DataFrame(all_it_contracts)
df_all_it_contracts = df_all_it_contracts[["uuid", "supplier", "systemUsages"]].copy()


flat_contracts = [flatten(d) for d in all_it_contracts]

df_flat_contracts = pd.DataFrame(flat_contracts)

# does not work
# flat = pd.json_normalize(df_all_it_contracts, sep=".")

want_contracts = df_flat_contracts[
    ["uuid", "systemUsages_0_uuid", "supplier_organization_uuid", "supplier_organization_name"]
].rename(
    columns={
        "uuid": "uuid_contract",
        "systemUsages_0_uuid": "uuid_usage",
        "supplier_organization_uuid": "uuid_leverandor",
        "supplier_organization_name": "leverandor",
    }
)

# all_it_contracts[19]["systemUsages"] Indeholder uuid key til it system, bortset fra index 19, som har 2 keys. Flere elementer har ingen keys.
# * 'uuid_contract', 'uuid_leverandor', 'leverandor'
df_all_it_contracts_partial = want_contracts

# ---------------------------------------------------------------------------- #
#                                  ! Big Merge                                 #
# ---------------------------------------------------------------------------- #

df_all_it_systems_partial  # pk: uuid_system, fk: none
df_it_system_usages_partial  # pk: uuid_usage, fk: uuid_system
df_all_it_contracts_partial  # pk: uuid_contract, fk: none

# Merge description from df_all_it_systems_partial into df_it_system_usages_partial
df_it_system_usages_partial = pd.merge(
    df_it_system_usages_partial, df_all_it_systems_partial, left_on="uuid_system", right_on="uuid_system", how="left"
)

# Merge leverandor from df_all_it_contracts_partial into df_it_system_usages_partial
df_it_system_usages_partial = pd.merge(
    df_it_system_usages_partial,
    df_all_it_contracts_partial,
    left_on="uuid_usage",
    right_on="uuid_usage",
    how="left",
).copy()


# Create new column. If system_name_local is not empty, then use system_name_local else use system_name
df_it_system_usages_partial["new_system_name"] = df_it_system_usages_partial.apply(
    lambda x: x["system_name_local"] if x["system_name_local"] else x["system_name"], axis=1
)

prefinal = df_it_system_usages_partial[
    [
        "new_system_name",
        "description",
        "leverandor",
        "ansvarlig_organisationsenhed",
        "relevante_organisationsenheder",
        "system_admins",
        "title_url_dict",
    ]
].copy()


# change prefinal["system_admins"] from list in cell to comma separated string in cell
prefinal["system_admins"] = prefinal["system_admins"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)

# title_url_dict cant be a dict
prefinal["title_url_dict"] = prefinal["title_url_dict"].apply(lambda x: json.dumps(x) if isinstance(x, dict) else x)

final = prefinal


# dump final to as data.json
final.to_json("path_to_webserver", orient="records", force_ascii=False)
