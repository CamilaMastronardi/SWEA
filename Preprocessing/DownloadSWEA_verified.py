# ============================================================
# Download SWEA data MAVEN L2 SVY3D
# ============================================================

import sys
import hashlib
import requests
from pathlib import Path
from datetime import datetime
from datetime import timedelta
from tqdm import tqdm


#------------------------------------------------------------
# Path for SWEA data
#------------------------------------------------------------

sweaPath = "swea_data"


#------------------------------------------------------------
# Function to build the SWEA CDF filename
#------------------------------------------------------------

def buildSWEAFilename(YYYY: str, MM: str, DD: str) -> str:
    """
    Builds the MAVEN SWEA L2 SVY3D CDF filename for a given date.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date in the format 'YYYY', 'MM', 'DD'.

    Returns
    -------
    str
        SWEA CDF filename.
    """

    filename = f"mvn_swe_l2_svy3d_{YYYY}{MM}{DD}_v05_r01.cdf"

    return filename


#------------------------------------------------------------
# Function to build the SWEA MD5 filename
#------------------------------------------------------------

def buildSWEAMD5Filename(YYYY: str, MM: str, DD: str) -> str:
    """
    Builds the MAVEN SWEA L2 SVY3D MD5 filename for a given date.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date in the format 'YYYY', 'MM', 'DD'.

    Returns
    -------
    str
        SWEA MD5 filename.
    """

    filename = f"mvn_swe_l2_svy3d_{YYYY}{MM}{DD}_v05_r01.md5"

    return filename


#------------------------------------------------------------
# Function to build the LASP base URL
#------------------------------------------------------------

def buildSWEABaseURL(YYYY: str, MM: str) -> str:
    """
    Builds the LASP directory URL for MAVEN SWEA L2 data.

    Parameters
    ----------
    YYYY, MM : str
        Year and month in the format 'YYYY', 'MM'.

    Returns
    -------
    str
        LASP base URL for the selected year and month.
    """

    base_url = f"https://lasp.colorado.edu/maven/sdc/public/data/sci/swe/l2/{YYYY}/{MM}/"

    return base_url


#------------------------------------------------------------
# Function to build the SWEA CDF URL
#------------------------------------------------------------

def buildSWEAURL(YYYY: str, MM: str, DD: str) -> str:
    """
    Builds the full LASP URL for a MAVEN SWEA L2 SVY3D CDF file.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date in the format 'YYYY', 'MM', 'DD'.

    Returns
    -------
    str
        Full URL of the SWEA CDF file.
    """

    base_url = buildSWEABaseURL(YYYY, MM)
    filename = buildSWEAFilename(YYYY, MM, DD)

    url = base_url + filename

    return url


#------------------------------------------------------------
# Function to build the SWEA MD5 URL
#------------------------------------------------------------

def buildSWEAMD5URL(YYYY: str, MM: str, DD: str) -> str:
    """
    Builds the full LASP URL for the official MD5 checksum file.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date in the format 'YYYY', 'MM', 'DD'.

    Returns
    -------
    str
        Full URL of the SWEA MD5 file.
    """

    base_url = buildSWEABaseURL(YYYY, MM)
    filename = buildSWEAMD5Filename(YYYY, MM, DD)

    url = base_url + filename

    return url


#------------------------------------------------------------
# Function to build the local SWEA file path
#------------------------------------------------------------

def buildSWEAFilePath(YYYY: str, MM: str, DD: str) -> Path:
    """
    Builds the local path where the SWEA CDF file will be stored.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date in the format 'YYYY', 'MM', 'DD'.

    Returns
    -------
    pathlib.Path
        Local path of the SWEA CDF file.
    """

    data_dir = Path(sweaPath)
    filename = buildSWEAFilename(YYYY, MM, DD)

    file_path = data_dir / filename

    return file_path


#------------------------------------------------------------
# Function to compute the MD5 checksum of a local file
#------------------------------------------------------------

def computeFileMD5(file_path: Path) -> str:
    """
    Computes the MD5 checksum of a local file.

    Parameters
    ----------
    file_path : pathlib.Path
        Path to the local file.

    Returns
    -------
    str
        MD5 checksum of the local file.
    """

    md5_hash = hashlib.md5()

    with open(file_path, "rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            md5_hash.update(chunk)

    return md5_hash.hexdigest()


#------------------------------------------------------------
# Function to download the official SWEA MD5 checksum
#------------------------------------------------------------

def getOfficialSWEAMD5(YYYY: str, MM: str, DD: str, timeout: int = 120) -> str:
    """
    Downloads the official MD5 checksum for a MAVEN SWEA L2 SVY3D CDF file.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date in the format 'YYYY', 'MM', 'DD'.

    timeout : int, optional
        Request timeout in seconds.

    Returns
    -------
    str
        Official MD5 checksum.
    """

    md5_url = buildSWEAMD5URL(YYYY, MM, DD)

    response = requests.get(md5_url, timeout=timeout)
    response.raise_for_status()

    md5_text = response.text.strip()
    official_md5 = md5_text.split()[0]

    return official_md5


#------------------------------------------------------------
# Function to check if the local SWEA file exists and is valid
#------------------------------------------------------------

def dataIsDownloaded(YYYY: str, MM: str, DD: str) -> bool:
    """
    Checks if the SWEA file already exists locally and if its MD5 matches
    the official LASP MD5 checksum.

    If the file exists but the MD5 does not match, the file is removed.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date in the format 'YYYY', 'MM', 'DD'.

    Returns
    -------
    bool
        True if the file exists and is valid, False otherwise.
    """

    file_path = buildSWEAFilePath(YYYY, MM, DD)

    if not file_path.exists():
        return False

    official_md5 = getOfficialSWEAMD5(YYYY, MM, DD)
    local_md5 = computeFileMD5(file_path)

    if local_md5 == official_md5:
        return True

    print("File exists but MD5 does not match. Removing damaged file.")
    print(f"Local MD5:    {local_md5}")
    print(f"Official MD5: {official_md5}")

    file_path.unlink()

    return False


#------------------------------------------------------------
# Function to download one file with a progress bar
#------------------------------------------------------------

def downloadFileWithProgress(
    url: str,
    temporary_file: Path,
    description: str,
    timeout: int = 300
):
    """
    Downloads a file using streaming and shows a progress bar.

    The file is written to a temporary '.part' file. This prevents damaged
    or incomplete downloads from being stored as final CDF files.

    Parameters
    ----------
    url : str
        File URL.

    temporary_file : pathlib.Path
        Temporary output file path.

    description : str
        Text shown in the progress bar.

    timeout : int, optional
        Request timeout in seconds.

    Returns
    -------
    None
    """

    headers = {"Accept-Encoding": "identity"}

    response = requests.get(
        url,
        stream=True,
        headers=headers,
        timeout=timeout
    )

    response.raise_for_status()

    print("URL:", url)
    print("Status code:", response.status_code)
    print("Content-Type:", response.headers.get("content-type"))
    print("Content-Length:", response.headers.get("content-length"))
    print("Content-Encoding:", response.headers.get("content-encoding"))

    total_size = int(response.headers.get("content-length", 0))

    with open(temporary_file, "wb") as file:
        with tqdm(
            total=total_size,
            unit="B",
            unit_scale=True,
            unit_divisor=1024,
            desc=description
        ) as progress_bar:

            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    file.write(chunk)
                    progress_bar.update(len(chunk))


#------------------------------------------------------------
# Function to download and validate a SWEA file
#------------------------------------------------------------

def downloadSWEAFile(YYYY: str, MM: str, DD: str, max_retries: int = 5):
    """
    Downloads the MAVEN SWEA L2 SVY3D CDF file for a given date.

    The file is downloaded as a temporary '.part' file. After each download
    attempt, the local MD5 is compared with the official LASP MD5. The final
    '.cdf' file is only created if the MD5 check passes.

    Parameters
    ----------
    YYYY, MM, DD : str
        Date in the format 'YYYY', 'MM', 'DD'.

    max_retries : int, optional
        Maximum number of download attempts if the MD5 check fails.

    Returns
    -------
    None
    """

    data_dir = Path(sweaPath)
    data_dir.mkdir(exist_ok=True)

    file_path = buildSWEAFilePath(YYYY, MM, DD)
    temporary_file = Path(str(file_path) + ".part")

    official_md5 = getOfficialSWEAMD5(YYYY, MM, DD)

    if dataIsDownloaded(YYYY, MM, DD):
        print("File already exists and MD5 is valid.")

        return

    url = buildSWEAURL(YYYY, MM, DD)

    for attempt in range(1, max_retries + 1):

        print("=" * 70)
        print(f"Downloading SWEA file {YYYY}-{MM}-{DD}")
        print(f"Attempt {attempt}/{max_retries}")
        print("=" * 70)

        if temporary_file.exists():
            temporary_file.unlink()

        downloadFileWithProgress(
            url=url,
            temporary_file=temporary_file,
            description=f"SWEA {YYYY}-{MM}-{DD}"
        )

        local_md5 = computeFileMD5(temporary_file)

        print(f"Local MD5:    {local_md5}")
        print(f"Official MD5: {official_md5}")

        if local_md5 == official_md5:
            temporary_file.rename(file_path)

            print("Download finished and MD5 is valid.")

            return

        print("MD5 check failed. Removing damaged temporary file.")
        temporary_file.unlink()

    raise ValueError(
        f"Could not download a valid SWEA file after {max_retries} attempts."
    )


#------------------------------------------------------------
# Function to build a list of dates between two dates
#------------------------------------------------------------

def getDates(initial_date, final_date):
    """
    Builds a list of dates between two dates.

    Parameters
    ----------
    initial_date : datetime.date
        Initial date.

    final_date : datetime.date
        Final date.

    Returns
    -------
    list
        List of datetime.date objects between initial_date and final_date,
        including both endpoints.
    """

    dates = []
    actual_date = initial_date

    while actual_date <= final_date:
        dates.append(actual_date)
        actual_date += timedelta(days=1)

    return dates


#------------------------------------------------------------
# Function to download SWEA files over a date range
#------------------------------------------------------------

def downloadSWEADataRange(
    initial_date,
    final_date,
    max_retries: int = 5
):
    """
    Downloads SWEA files for a date range.

    Parameters
    ----------
    initial_date : datetime.date
        Initial date.

    final_date : datetime.date
        Final date.

    max_retries : int, optional
        Maximum number of download attempts for each daily file.

    Returns
    -------
    None
    """

    dates = getDates(initial_date, final_date)

    print(f"Downloading files in range {initial_date} - {final_date}")

    for i, actual_date in enumerate(dates, start=1):
        print(f"Downloading day {i} of {len(dates)}")

        downloadSWEAFile(
            actual_date.strftime("%Y"),
            actual_date.strftime("%m"),
            actual_date.strftime("%d"),
            max_retries=max_retries
        )


#------------------------------------------------------------
# Main function to handle command line arguments and download files
#------------------------------------------------------------

if __name__ == "__main__":

    if len(sys.argv) not in (2, 3, 4):
        print("I use:")
        print("python3 DownloadSWEA.py YYYY-MM-DD")
        print("python3 DownloadSWEA.py YYYY_i-MM_i-DD_i YYYY_f-MM_f-DD_f")
        print("python3 DownloadSWEA.py YYYY_i-MM_i-DD_i YYYY_f-MM_f-DD_f max_retries")
        sys.exit(1)

    if len(sys.argv) == 2:
        date = sys.argv[1]
        YYYY, MM, DD = date.split("-")

        downloadSWEAFile(YYYY, MM, DD)

        print("Finished")

    elif len(sys.argv) in (3, 4):
        initial_parameter = sys.argv[1]
        final_parameter = sys.argv[2]

        YYYY_i, MM_i, DD_i = (int(f) for f in initial_parameter.split("-"))
        YYYY_f, MM_f, DD_f = (int(f) for f in final_parameter.split("-"))

        initial_date = datetime(YYYY_i, MM_i, DD_i).date()
        final_date = datetime(YYYY_f, MM_f, DD_f).date()

        max_retries = 5

        if len(sys.argv) == 4:
            max_retries = int(sys.argv[3])

        downloadSWEADataRange(
            initial_date,
            final_date,
            max_retries=max_retries
        )

        print("Finished")
