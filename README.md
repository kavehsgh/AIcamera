  # AIcamera1
AIcamera1 -- For Towing Companies 

# AIcamera project branches
main  
v1  
v1-plate  
  
there will be one branch for each feature

# King_Kong1 image folders

image name format: year-month-day_hour:minute:second"AM/PM"_weekday_imagetype  
example: 2024-06-21_08:54:47AM_Friday_overlay

Raw images of detections: data/raw  
Overlayed images of detection: data/car/overlayed  
Cropped images of detections: data/cara/cropped


# King_Kong recorded images in S3 bucket (just overlay images)
https://us-west-2.console.aws.amazon.com/s3/buckets


# Connecting to King_Kong with SSH on Ubuntu

This guide will walk you through the steps required to connect to your hardware using SSH on an Ubuntu system. You need to ask for an openvpn config file `filename.ovpn` from an admin.

## Prerequisites

Before you start, ensure that you have the following installed on your Ubuntu system:

1. **OpenSSH Client**: The SSH client is typically pre-installed on Ubuntu. You can check its installation by running:

    ```bash
    ssh -V
    ```

    If it's not installed, you can install it with:

    ```bash
    sudo apt update
    sudo apt install openssh-client
    ```

2. **Network Tools**: Tools like `ping` and `net-tools` are useful for network diagnostics.
    ```bash
    sudo apt install net-tools
    ```

3. **OpenVPN**: To use VPN for connecting to the King_Kong.
    ```bash
    sudo apt install openvpn
    ```

4. **Geditor**: To edit some config files.
    ```bash
    sudo apt install gedit
    ```

## Step-by-Step Instructions


1. **Copy the OpenVPN configuration file to the OpenVPN directory**. Make sure the file is in the home directory.
    ```bash
    sudo cp ~/<filename>.ovpn /etc/openvpn/<filename>.conf
    ```

2. **Start the OpenVPN client using your configuration file:**
    ```bash
    sudo openvpn --config /etc/openvpn/<filename>.conf
    ```

3. **Add an entry to your /etc/hosts file to resolve the King_Kong's hostname:**
    ```bash
    sudo gedit /etc/hosts
    ```

    Add the following line to the file and save it. Add a number to the end of the king_kong. 1 and 2 is occupied. example: king_kong4

    ```
    10.8.0.[IP] king_kong[a number]
    ```

4. **Generate an SSH key pair if you don't have one already:**
    ```bash
    ssh-keygen
    ```

    Follow the prompts to save the key pair to the default location (~/.ssh/id_rsa).


5. **Copy your public SSH key to the clipboard to share with the admin (or use another method to transfer it):**
    ```bash
    cat ~/.ssh/id_rsa.pub
    ```

    Provide the output to the admin who will add it to the King_Kong's ~/.ssh/authorized_keys.


6. **Verify that your SSH configuration file exists (optional but recommended for managing multiple connections):**
    ```bash
    gedit ~/.ssh/config
    ```  

    Add the following entry for your Raspberry Pi:

    ```bash
    Host king_kong[the number you entered on step 3]
        HostName 10.8.0.[IP]
        User pi
    ```  

7. **Check the connectivity to the VPN server (optional):**
    ```bash
    ping 10.8.0.1
    ```  

8. **Connect to the King_Kong using its IP address:**
    ```bash
    ssh pi@10.8.0.[IP]
    ```  

9. **Alternatively, connect to the King_Kong using the hostname (if configured in ~/.ssh/config):**
    ```bash
    ssh pi@king_kong[the number you entered on step 3]
    ```

    or simply:

    ```bash
    ssh king_kong[the number you entered on step 3]
    ```




