# Creepyr: A cli Minecraft launcher/server-launcher/pack-dev-tool written in Python by Dunkmania101

import minecraft_launcher_lib
import subprocess
import sys
import socket
import requests
from logging import getLogger
from typing import Union
from os import path as ospath
from json import dumps as jdumps, loads as jloads
from uuid import uuid1 as randuuid


logger = getLogger("creepyr")

global cf_api_key
cf_api_key: str = ""


def expand_full_path(pathstr: str) -> str:
    return ospath.expanduser(ospath.expandvars(pathstr))

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

    def __init__(self, name: str = "minecraft", mcdir: str = minecraft_launcher_lib.utils.get_minecraft_directory(), mcversion: str =  "", mctype: str = "vanilla", mlversion: str = "", jvmexec: str = "", jvmargs: list[str] = [], verify_mcversion: bool = True, verify_mlversion: bool = True, verify_launch_version: bool = True, manifest_path: Union[str, None] = None) -> None:
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
            elif mctype == "fabric" and minecraft_launcher_lib.fabric.is_minecraft_version_supported(mcversion):
                if has_network_access():
                    mlversion = minecraft_launcher_lib.fabric.get_latest_loader_version()
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
        self.manifest_path = manifest_path

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

    def install_mods_cf(self, api_key: str) -> bool:
        if self.manifest_path is not None:
            jfilepath = expand_full_path(self.manifest_path)
            with open(jfilepath, "rb") as f:
                manifest_data = jloads(f.read())
                modslist = manifest_data.get("files", [])
                for jmod in modslist:
                    try:
                        modurl = requests.get(f"https://api.curseforge.com/v1/mods/{jmod.get('projectID', '')}/files/{jmod.get('fileID', '')}/download-url", headers = {
                            "Accept": "application/json",
                            "x-api-key": api_key,}).json().get("data")
                    except:
                        modurl = None
                    if modurl is not None:
                        moddl = requests.get(modurl, stream=True)
                        modfilename = modurl.split("/")[-1]
                        msg = f"Saving {modfilename} from url: {modurl}..."
                        logger.info(msg)
                        print(msg)
                        with open(expand_full_path(ospath.join(self.get_mcdir_path(), "mods", modfilename)), "wb") as modfile:
                            total_length = int(moddl.headers.get("content-length"))
                            chunk_size = 2391975
                            for i, ch in enumerate(moddl.iter_content(chunk_size=chunk_size)):
                                if ch:
                                    msg = f"Saving chunk {i*chunk_size}/{total_length} to {modfilename}..."
                                    logger.info(msg)
                                    print(msg)
                                    modfile.write(ch)
        return True

    def install_mods(self) -> bool:
        return self.install_mods_cf(cf_api_key)

    def install(self) -> bool:
        return self.install_mc() and self.install_mods()

    def update_mc(self) -> bool:
        return False

    def update(self) -> bool:
        return False

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
                "manifest_path": self.manifest_path,
                }

    @staticmethod
    def from_dict(data: dict):
        return Instance(data.get("name", ""), data.get("mcdir", ""), data.get("mcversion", ""), data.get("mctype", ""), data.get("mlversion", ""), data.get("jvmexec", ""), data.get("jvmargs", ""), data.get("verify_mcversion", True), data.get("verify_mlversion", True), data.get("verify_launch_version", True), data.get("manifest_path", None))

    def __str__(self) -> str:
        return str(self.to_dict())


def main(args: list[str]) -> int:
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
            if ospath.isfile(jfilepath):
                with open(jfilepath, "r") as f:
                    instance = Instance.from_dict(jloads(f.read()))
                    instanceargs = instanceargs[1:]
        if instance is None:
            iscreate = instanceargs[0] == "create"
            logger.error("Could not " + ("create" if iscreate else "load") + " instance!")
            return 1 if iscreate else -1
        else:
            if args[2] == "create":
                jfilepath = expand_full_path(instanceargs[0])
                try:
                    with open(jfilepath, "w+") as f:
                        f.write(jdumps(instance.to_dict(), indent=4))
                except Exception as e:
                    logger.error(f"Could not save instance to file {jfilepath}: ", e)
            elif args[2] == "install":
                return 0 if instance.install() else 1
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
                    if ospath.isfile(jfilepath):
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
            if ospath.isfile(jfilepath):
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
    return 0


if __name__ == "__main__":
    exit(main(sys.argv))

