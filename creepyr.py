# Creepyr: A CLI Minecraft launcher/server-launcher/pack-dev-tool written in Python by Dunkmania101


# License:
"""
MIT License

Copyright (c) 2022 Duncan Brasher (Dunkmania101)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""



import minecraft_launcher_lib
import subprocess
import sys
import os
import socket
import requests
from logging import getLogger
from typing import Union
from json import dumps as jdumps, loads as jloads
from threading import Thread
from uuid import uuid1 as randuuid


logger = getLogger("creepyr")

global cf_api_key
cf_api_key: str = ""


def expand_full_path(pathstr: str) -> str:
    return os.path.expanduser(os.path.expandvars(pathstr))

def has_network_access() -> bool:
    return not socket.gethostbyname(socket.gethostname()).startswith(("127.", "172."))


class Account():
    def __init__(self, name: str = "fake", username: str = "fake", mcuuid: str = "", mctoken: str = "") -> None:
        self.name = name
        self.username = username
        if mcuuid == "":
            mcuuid = str(randuuid())
        self.mcuuid = mcuuid
        self.mctoken = mctoken

    def get_account_type(self) -> str:
        return "offline"

    def login(self, credentials: dict) -> bool:
        return True

    def is_logged_in(self) -> bool:
        return False

    def to_dict(self) -> dict:
        return {
                "name": self.name,
                "username": self.username,
                "mcuuid": self.mcuuid,
                "mctoken": self.mctoken,
                }

    def to_options(self) -> dict:
        return {
                "username": self.username,
                "uuid": self.mcuuid,
                "token": self.mctoken,
                }

    @staticmethod
    def from_dict(data: dict):
        return Account(data.get("name", ""), data.get("username", ""), data.get("mcuuid", ""), data.get("mctoken", ""))

    def __str__(self) -> str:
        return str(self.to_dict())


#class MojangAccount(Account):
#    def __init__(self, name: str = "fake", username: str = "fake", mcuuid: str = "") -> None:
#        super().__init__(name, username, mcuuid)
#
#    def get_account_type(self) -> str:
#        return "mojang"
#
#
#class MicrosoftAccount(Account):
#    def __init__(self, name: str = "fake", username: str = "fake", mcuuid: str = "") -> None:
#        super().__init__(name, username, mcuuid)
#
#    def get_account_type(self) -> str:
#        return "microsoft"


class Instance():
    current_install_max: int = 0

    def __init__(self, name: str = "minecraft", mcdir: str = minecraft_launcher_lib.utils.get_minecraft_directory(), mcversion: str =  "", mctype: str = "vanilla", mlversion: str = "", jvmexec: str = "", jvmargs: list[str] = [], verify_mcversion: bool = True, verify_mlversion: bool = True, verify_launch_version: bool = True, cf_manifest_path: Union[str, None] = None, mr_manifest_path: Union[str, None] = None, creepyr_manifest_path: Union[str, None] = None) -> None:
        self.verify_mcversion: bool = verify_mcversion
        self.verify_mlversion: bool = verify_mlversion
        self.verify_launch_version: bool = verify_launch_version
        self.name: str = name
        self.mcdir: str = mcdir
        if mcversion == "":
            if has_network_access():
                mcversion = minecraft_launcher_lib.utils.get_latest_version()["release"]
            else:
                logger.warning(f"Could not connect to the internet while trying to get latest Minecraft version: {mlversion}    ; Setting it to the string \"Invalid\"")
        elif self.verify_mcversion:
            msg = f"Verifying Minecraft version: {mcversion} ..."
            logger.info(msg)
            print(msg)
            if has_network_access():
                if not minecraft_launcher_lib.utils.is_vanilla_version(mcversion):
                    logger.error(f"Minecraft version {mlversion} is invalid!")
                    mcversion = ""
            else:
                logger.warning(f"Could not connect to the internet while trying to verify Forge version: {mlversion}    ; Proceeding under the assumption it is correct!")
        else:
            mcversion = mcversion
        if mcversion == "":
            self.mcversion: str = "Invalid"
        else:
            self.mcversion: str = mcversion
        if mctype in ("vanilla", "forge", "fabric"):
            self.mctype: str = mctype
        else:
            self.mctype: str = "Invalid"
        if mlversion == "":
            if mctype == "forge":
                if has_network_access():
                    fgversion = minecraft_launcher_lib.forge.find_forge_version(mcversion)
                    if fgversion is not None:
                        mlversion = fgversion
                    else:
                        logger.warning(f"Could not find a valid Forge version for Minecraft version: {mcversion}    ; Setting it to the string \"Invalid\"")
                else:
                    logger.warning(f"Could not connect to the internet while trying to get latest Forge version: {mlversion}    ; Setting it to the string \"Invalid\"")
            elif mctype == "fabric":
                if has_network_access():
                    if minecraft_launcher_lib.fabric.is_minecraft_version_supported(mcversion):
                        mlversion = minecraft_launcher_lib.fabric.get_latest_loader_version()
                    else:
                        logger.warning(f"Could not find a valid Fabric version for Minecraft version: {mcversion}    ; Setting it to the string \"Invalid\"")
                else:
                    logger.warning(f"Could not connect to the internet while trying to get latest Fabric version: {mlversion}    ; Setting it to the string \"Invalid\"")
        elif self.verify_mlversion:
            if mctype == "forge":
                msg = f"Verifying Forge version: {mlversion} ..."
                logger.info(msg)
                print(msg)
                if has_network_access():
                    if not minecraft_launcher_lib.forge.is_forge_version_valid(mlversion):
                        logger.error(f"Forge version {mlversion} is invalid!")
                        mlversion = ""
                else:
                    logger.warning(f"Could not connect to the internet while trying to verify Forge version: {mlversion}    ; Proceeding under the assumption it is correct!")
            else:
                if not minecraft_launcher_lib.fabric.is_minecraft_version_supported(mcversion):
                    logger.warning(f"Fabric version: {mlversion}    is invalid for Minecraft version: {mcversion}    ; Setting it to the string \"Invalid\"")
                else:
                    mlversion = mlversion
        else:
            mlversion = mlversion
        if mlversion == "":
            self.mlversion: str = "Invalid"
        else:
            self.mlversion: str = mlversion
        self.jvmexec: str = jvmexec
        self.jvmargs: list[str] = jvmargs
        self.cf_manifest_path: Union[str, None] = cf_manifest_path
        self.mr_manifest_path: Union[str, None] = mr_manifest_path
        self.creepyr_manifest_path: Union[str, None] = creepyr_manifest_path

    def get_mcdir_path(self):
        return expand_full_path(self.mcdir)

    def get_jvmexec_path(self):
        return expand_full_path(self.jvmexec)

    def install_mc(self) -> bool:
        if has_network_access():
            try:
                if self.mctype == "forge":
                    minecraft_launcher_lib.forge.install_forge_version(self.mlversion, self.get_mcdir_path(), callback=self.get_install_callbacks())
                elif self.mctype == "fabric":
                    minecraft_launcher_lib.fabric.install_fabric(self.mcversion, self.get_mcdir_path(), callback=self.get_install_callbacks())
                else:
                    minecraft_launcher_lib.install.install_minecraft_version(self.mcversion, self.get_mcdir_path(), callback=self.get_install_callbacks())
                return True
            except Exception as e:
                logger.warning(e)
                return False
        else:
            logger.warning(f"Could not connect to the internet while trying to verify Minecraft version: {self.mcversion}    , of type: {self.mctype}{'' if self.mctype == 'vanilla' else '    , and of loader version: ' + self.mlversion}    ; Exiting with code 1!")
            return False

    def set_install_status(self, status: str):
        logger.info(status)
        print(status)

    def set_install_progress(self, progress: int):
        if self.current_install_max != 0:
            msg = f"{progress}/{self.current_install_max}"
            logger.info(msg)
            print(msg)
    
    def set_install_max(self, new_max: int):
        self.current_install_max = new_max

    def get_install_callbacks(self) -> dict:
        return {
            "setStatus": self.set_install_status,
            "setProgress": self.set_install_progress,
            "setMax": self.set_install_max,
        }

    def install_mod_mr(self, jmod: dict, ithread: Union[int, None] = None, imod: Union[int, None] = None, ithreads: Union[int, None] = None, imods: Union[int, None] = None, total_imods: Union[int, None] = None) -> bool:
        return True

    def install_mod_cf(self, jmod: dict, api_key: str, ithread: Union[int, None] = None, imod: Union[int, None] = None, ithreads: Union[int, None] = None, imods: Union[int, None] = None, total_imods: Union[int, None] = None) -> bool:
        try:
            modurl = requests.get(f"https://api.curseforge.com/v1/mods/{jmod.get('projectID', '')}/files/{jmod.get('fileID', '')}/download-url", headers = {
                "Accept": "application/json",
                "x-api-key": api_key,}, timeout=60).json().get("data")
        except Exception as e:
            logger.warning(f"Encountered exception while finding mod: {jmod}: ", e)
            modurl = None
        if modurl is not None:
            try:
                moddl = requests.get(modurl, stream=True, timeout=60*3)
                modfilename = modurl.split("/")[-1]
                modfilepath = expand_full_path(os.path.join(self.get_mcdir_path(), "mods", modfilename))
                if ithread is not None and ithread is not None:
                    iprefix = f"[ Thread {ithread}/{ithreads} ]: "
                else:
                    iprefix = ""
                if imod is not None and imods is not None:
                    iprefix += f"[ Mod {imod}/{imods}{', In Total '+ str(total_imods) if total_imods is not None else ''} ]: "
                if os.path.isfile(modfilepath):
                    msg = f"{iprefix}File {modfilepath} already exists, skipping..."
                    logger.info(msg)
                    print(msg)
                else:
                    msg = f"{iprefix}Saving {modfilename} from url: {modurl} to: {modfilepath}..."
                    logger.info(msg)
                    print(msg)
                    os.makedirs(expand_full_path(os.path.join(self.get_mcdir_path(), "mods")), exist_ok=True)
                    with open(modfilepath, "wb") as modfile:
                        total_length = int(moddl.headers.get("content-length"))
                        chunk_size = 2391975
                        for chi, ch in enumerate(moddl.iter_content(chunk_size=chunk_size)):
                            if ch:
                                msg = f"Saving chunk {chi*chunk_size}/{total_length} to {modfilename} at: {modfilepath}..."
                                logger.info(msg)
                                print(msg)
                                modfile.write(ch)
            except Exception as e:
                logger.warning(f"Encountered exception while downloading mod: {jmod}: ", e)
        return True

    def _sub_install_mods_cf(self, api_key: str, modslist: list, ithread: int, ithreads: int, total_imods: int) -> bool:
        ret = True
        for imod, jmod in enumerate(modslist):
            if not self.install_mod_cf(jmod, api_key, ithread, imod+1, ithreads, len(modslist), total_imods):
                ret = False
        return ret

    def install_mods_cf(self, api_key: str, threads: int = 10) -> bool:
        if self.cf_manifest_path is not None:
            jfilepath = expand_full_path(self.cf_manifest_path)
            if os.path.isfile(jfilepath):
                with open(jfilepath, "r") as f:
                    manifest_data = jloads(f.read())
                    modslist = manifest_data.get("files", [])
                    thread_size = max(int(len(modslist) / threads), 1)
                    last_ithread = 0
                    for ithread in range(1, threads+1):
                        next_ithread = last_ithread+thread_size
                        Thread(target=self._sub_install_mods_cf, args=[api_key, modslist[last_ithread:(None if ithread >= threads else next_ithread)], ithread, threads, len(modslist)]).start()
                        if next_ithread >= len(modslist):
                            break
                        last_ithread = next_ithread
        return True

    def install_mods_mr(self, threads: int = 10) -> bool: # TODO
        #if self.mr_manifest_path is not None:
        #    jfilepath = expand_full_path(self.mr_manifest_path)
        #    if os.path.isfile(jfilepath):
        #        with open(jfilepath, "r") as f:
        #            manifest_data = jloads(f.read())
        return True

    def install_mods(self) -> bool:
        return self.install_mods_cf(cf_api_key)

    def install(self) -> bool:
        return self.install_mc() and self.install_mods()

    def update_mc(self, save: bool = True, jfilepath: Union[str, None] = None) -> bool:
        if has_network_access():
            latest_mcversion = minecraft_launcher_lib.utils.get_latest_version()["release"]
            if self.mcversion != latest_mcversion:
                self.mcversion = latest_mcversion
                if save:
                    return self.save_to_file(jfilepath)
                return True
            else:
                logger.warning(f"{self.mcversion} is already up to date!")
        return False

    def update_ml(self, save: bool = True, jfilepath: Union[str, None] = None) -> bool:
        if has_network_access():
            if self.mctype == "forge":
                fgversion = minecraft_launcher_lib.forge.find_forge_version(self.mcversion)
                if fgversion is not None:
                    latest_mlversion = fgversion
                else:
                    logger.warning(f"Could not find a valid Forge version for Minecraft version: {self.mcversion}    ; Setting it to the string \"Invalid\"")
                    return False
            elif self.mctype == "fabric":
                if minecraft_launcher_lib.fabric.is_minecraft_version_supported(self.mcversion):
                    latest_mlversion = minecraft_launcher_lib.fabric.get_latest_loader_version()
                else:
                    logger.warning(f"Could not find a valid Fabric version for Minecraft version: {self.mcversion}    ; Setting it to the string \"Invalid\"")
                    return False
            else:
                return False
            if self.mlversion != latest_mlversion:
                self.mlversion = latest_mlversion
                if save:
                    return self.save_to_file(jfilepath)
                return True
            else:
                logger.warning(f"{self.mlversion} is already up to date!")
        return False

    def update(self, save: bool = True, jfilepath: Union[str, None] = None) -> bool:
        if self.mctype == "vanilla":
            return self.update_mc(save, jfilepath)
        else:
            return self.update_ml(save, jfilepath)

    def get_launch_cmd(self, account: Account, jvmexec: str = "", jvmargs: list[str] = [], verify_launch_version: Union[bool, None] = None) -> Union[list[str], int]:
        if verify_launch_version is None:
            verify_launch_version = self.verify_launch_version
        options = account.to_options()
        if jvmexec == "":
            jvmexec = self.get_jvmexec_path()
        options["executablePath"] = expand_full_path(jvmexec)
        if len(jvmargs) > 0:
            options["jvmArguments"] = jvmargs
        if self.mctype == "vanilla":
            version = self.mcversion
        elif self.mctype == "forge":
            version = minecraft_launcher_lib.forge.forge_to_installed_version(self.mlversion)
        else:
            version = f"{self.mcversion}-{self.mctype}-{self.mlversion}" # This should handle Fabric
        vn_valid = not verify_launch_version
        if not vn_valid:
            for vn in minecraft_launcher_lib.utils.get_installed_versions(self.get_mcdir_path()):
                if version == vn["id"]:
                    vn_valid = True
                    break
        if vn_valid:
            return minecraft_launcher_lib.command.get_minecraft_command(version, self.get_mcdir_path(), options)
        else:
            logger.error(f"Failed to launch Minecraft of type: {self.mctype}    and of version: {version}    because that version is not installed! Exiting with code -1.")
            return -1

    def launch(self, account: Account, jvmexec: str = "", jvmargs: list[str] = [], verify_launch_version: Union[bool, None] = None) -> int:
        if verify_launch_version is None:
            verify_launch_version = self.verify_launch_version
        if len(minecraft_launcher_lib.utils.get_installed_versions(self.get_mcdir_path())) == 0:
            if not self.install_mc():
                return 1
        if jvmexec == "":
            jvmexec = self.get_jvmexec_path()
        launch_cmd = self.get_launch_cmd(account, jvmexec, jvmargs, verify_launch_version)
        if isinstance(launch_cmd, list):
            return subprocess.call(launch_cmd, cwd=self.get_mcdir_path())
        return launch_cmd

    def to_dict(self) -> dict:
        return {
                "name": self.name,
                "mcdir": self.mcdir,
                "mcversion": self.mcversion,
                "mctype": self.mctype,
                "mlversion": self.mlversion,
                "jvmexec": self.jvmexec,
                "jvmargs": self.jvmargs,
                "verify_mcversion": self.verify_mcversion,
                "verify_mlversion": self.verify_mlversion,
                "verify_launch_version": self.verify_launch_version,
                "cf_manifest_path": self.cf_manifest_path,
                "mr_manifest_path": self.mr_manifest_path,
                "creepyr_manifest_path": self.creepyr_manifest_path,
                }

    @staticmethod
    def from_dict(data: dict):
        return Instance(data.get("name", ""), data.get("mcdir", ""), data.get("mcversion", ""), data.get("mctype", ""), data.get("mlversion", ""), data.get("jvmexec", ""), data.get("jvmargs", ""), data.get("verify_mcversion", True), data.get("verify_mlversion", True), data.get("verify_launch_version", True), data.get("cf_manifest_path", None), data.get("mr_manifest_path", None), data.get("creepyr_manifest_path", None))

    def save_to_file(self, jfilepath: Union[str, None] = None) -> bool:
        if jfilepath is None:
            jfilepath = self.creepyr_manifest_path
        if jfilepath is not None:
            try:
                jfilepath = expand_full_path(jfilepath)
                with open(jfilepath, "w+") as f:
                    f.write(jdumps(self.to_dict(), indent=4))
                    return True
            except Exception as e:
                logger.error(f"Could not save instance to file {jfilepath}: ", e)
        return False

    def __str__(self) -> str:
        return str(self.to_dict())


def main(args: list[str]) -> int:
    help_msg = """
    Creepyr: A CLI Minecraft launcher/server-launcher/pack-dev-tool written in Python by Dunkmania101



    Basic usage:


    ```
    # Launch
    python3 creepyr.py instance run stdin LOCAL_NAME MINECRAFT_DIR MINECRAFT_VERSION \\
    MINECRAFT_TYPE \\ # One of: vanilla, forge, fabric
    MOD_LOADER_VERSION \\ # "" if using vanilla
    JVM_EXEC \\ # Likely /usr/lib/jvm/default/bin/java on Unix-like systems
    JVM_ARGS \\ # Needs to be in quotes as one long, space-delimited string
    stdin LOCAL_ACCOUNT_NAME USERNAME UUID TOKEN
    ```


    ```
    # Print this help message
    python3 creepyr.py help
    ```


    See https://github.com/Dunkmania101/Creepyr for more
    """
    arg_cfapikey = "cfapikey="
    for arg in args:
        if arg.startswith(arg_cfapikey):
            global cf_api_key
            cf_api_key = arg.removeprefix(arg_cfapikey)
            args.remove(arg)
    if args[1] == "instance":
        instanceargs = args[3:]
        instance = None
        if instanceargs[0] in ("stdin", "create"):
            instance = Instance(instanceargs[1], instanceargs[2], instanceargs[3], instanceargs[4], instanceargs[5], instanceargs[6], instanceargs[7].split(" "))
            instanceargs = instanceargs[8:]
        else:
            jfilepath = expand_full_path(instanceargs[0])
            if os.path.isfile(jfilepath):
                with open(jfilepath, "r") as f:
                    instance = Instance.from_dict(jloads(f.read()))
                    instance.creepyr_manifest_path = jfilepath
                    instanceargs = instanceargs[1:]
        if instance is None:
            iscreate = instanceargs[0] == "create"
            logger.error("Could not " + ("create" if iscreate else "load") + " instance!")
            return 1 if iscreate else -1
        else:
            if args[2] == "create":
                jfilepath = expand_full_path(instanceargs[0])
                return 0 if instance.save_to_file(jfilepath) else 1
            elif args[2] == "install":
                return 0 if instance.install() else 1
            elif args[2] == "install-mc":
                return 0 if instance.install_mc() else 1
            elif args[2] == "install-mods":
                return 0 if instance.install_mods() else 1
            elif args[2] == "install-mods-cf":
                return 0 if instance.install_mods_cf(cf_api_key) else 1
            elif args[2] == "install-mods-mr":
                return 0 if instance.install_mods_mr() else 1
            elif args[2] == "install-mod-cf":
                return 0 if instance.install_mod_mr({}) else 1
            elif args[2] == "install-mod-cf":
                return 0 if instance.install_mod_cf({"projectID": instanceargs[0], "fileID": instanceargs[1]}, cf_api_key) else 1
            elif args[2] == "update":
                jfilepath = expand_full_path(args[3])
                return 0 if instance.update(jfilepath=jfilepath) else 1
            elif args[2] == "update-mc":
                jfilepath = expand_full_path(args[3])
                return 0 if instance.update_mc(jfilepath=jfilepath) else 1
            elif args[2] == "update-ml":
                jfilepath = expand_full_path(args[3])
                return 0 if instance.update_ml(jfilepath=jfilepath) else 1
            elif args[2] == "run":
                runargs = instanceargs[0:]
                msg = "Running instance: " + str(instance)
                logger.info(msg)
                print(msg)
                account = None
                if runargs[0] == "stdin":
                    account = Account(runargs[1], runargs[2], runargs[3], runargs[4])
                else:
                    jfilepath = expand_full_path(runargs[0])
                    if os.path.isfile(jfilepath):
                        with open(jfilepath, "r") as f:
                            account = Account.from_dict(jloads(f.read()))
                if account is None:
                    iscreate = runargs[0] == "stdin"
                    logger.error("Could not " + ("create" if iscreate else "load") + " instance!")
                    return 1 if iscreate else -1
                else:
                    if len(runargs) >= 9:
                        jvmexec = runargs[10]
                    else:
                        jvmexec = instance.jvmexec
                    if len(runargs) >= 10:
                        jvmargs = runargs[11].split(" ")
                    else:
                        jvmargs = instance.jvmargs
                    exit_code = instance.launch(account, jvmexec, jvmargs)
                    if exit_code == 0:
                        msg = "Game exited normally with code 0"
                        logger.info("Game exited normally with code 0")
                        print(msg)
                        return exit_code
                    else:
                        return_code = 100 + exit_code
                        return_code = return_code if return_code != 0 else exit_code
                        logger.error(f"Game exited abnormally with code {exit_code}, exiting with code {return_code} (100+{exit_code})")
                        return return_code
    elif args[1] == "account":
        accountargs = args[2:]
        account = None
        if accountargs[0] in ("stdin", "create"):
            account = Account(accountargs[1], accountargs[2], accountargs[3], accountargs[4])
            accountargs = accountargs[5:]
        else:
            jfilepath = expand_full_path(accountargs[1])
            if os.path.isfile(jfilepath):
                with open(jfilepath, "r") as f:
                    account = Account.from_dict(jloads(f.read()))
        if account is None:
            iscreate = accountargs[0] == "create"
            logger.error("Could not " + ("create" if iscreate else "load") + " account!")
            return 1 if iscreate else -1
        else:
            if args[2] == "create":
                jfilepath = expand_full_path(accountargs[0])
                try:
                    with open(jfilepath, "w+") as f:
                        f.write(jdumps(account.to_dict(), indent=4))
                except Exception as e:
                    logger.error(f"Could not save instance to file {jfilepath}: ", e)
    else:
        if args[1] not in ("help", "h", "--help", "-h", "-help"):
            logger.warning(f"Invalid arguments: {args[1:]}")
        logger.info(help_msg)
        print(help_msg)
    return 0


if __name__ == "__main__":
    exit(main(sys.argv))

