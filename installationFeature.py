import os
import requests
import shutil
import subprocess
import tempfile
import tkinter as tk
import webbrowser
import winreg
from tkinter import filedialog, messagebox

class InstallationFeature:
    def __init__(self, translator, result_textbox=None):
        self.translator = translator
        self.result_textbox = result_textbox

    def textbox(self, message):
        self.result_textbox.config(state="normal")
        self.result_textbox.insert(tk.END, message + "\n")
        self.result_textbox.config(state="disable")
        self.result_textbox.update_idletasks()  # 刷新界面

    def download_from_winget(self):
        try:
            # 检查 WinGet 是否安装
            result = subprocess.Popen(['where.exe', 'winget.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            stdout, stderr = result.communicate()
            if result.returncode != 0:
                return self.translator.translate("winget_not_installed")

            # 弹出提示框询问用户是否同意 Microsoft Store 源协议
            self.textbox(self.translator.translate("winget_msstore_source_agreement") + '\n')
            response = messagebox.askyesnocancel(
                self.translator.translate("winget_msstore_source_agreement_notice"),
                self.translator.translate("ask_winget_msstore_source_agreement")
            )
            if response is None:
                return self.translator.translate("user_canceled")
            elif not response:
                return self.translator.translate("disagree_winget_msstore_source_agreement")

            # 使用 WinGet 搜索 Microsoft PC Manager
            result = subprocess.Popen(['winget.exe', 'search', 'Microsoft PC Manager', '--source', 'msstore', '--accept-source-agreements'],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            stdout, stderr = result.communicate()
            if result.returncode != 0:
                if result.returncode == 2316632067:
                    return self.translator.translate("winget_not_internet_connection")
                elif result.returncode == 2316632084:
                    return self.translator.translate("winget_no_results_found")
                elif result.returncode == 2316632139:
                    return self.translator.translate("winget_source_reset_needed")
                else:
                    stderr = stderr.strip() if stderr else self.translator.translate("winget_not_error_info")
                    stdout = stdout.strip() if stdout else self.translator.translate("winget_not_output")
                    return f"{self.translator.translate('winget_error')}\n{self.translator.translate('winget_error_info')}: {stderr}\n{self.translator.translate('winget_error_code')}: {result.returncode}\n{self.translator.translate('winget_output')}: {stdout}"

            # 使用 WinGet 安装 Microsoft PC Manager
            result = subprocess.Popen(['winget.exe', 'install', 'Microsoft PC Manager', '--source', 'msstore', '--accept-source-agreements', '--accept-package-agreements'],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            stdout, stderr = result.communicate()
            self.textbox(self.translator.translate("downloading_pc_manager_from_winget") + '\n')
            if result.returncode != 0:
                if result.returncode == 2316632107:
                    return self.translator.translate("already_installed_pc_manager_from_winget")
                else:
                    stderr = stderr.strip() if stderr else self.translator.translate("winget_not_error_info")
                    stdout = stdout.strip() if stdout else self.translator.translate("winget_not_output")
                    return f"{self.translator.translate('winget_error')}\n{self.translator.translate('winget_error_info')}: {stderr}\n{self.translator.translate('winget_error_code')}: {result.returncode}\n{self.translator.translate('winget_output')}: {stdout}"

            return self.translator.translate("pc_manager_has_been_installed_from_winget")
        except Exception as e:
            return f"{self.translator.translate('winget_error')}\n{self.translator.translate('winget_error_info')}: {str(e)}\n{self.translator.translate('winget_not_error_code')}"

    def download_from_msstore(self):
        try:
            # 检测 Microsoft Store 是否安装
            result = subprocess.run(
                ['powershell.exe', '-Command', 'Get-AppxPackage -Name Microsoft.WindowsStore'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            if 'PackageFamilyName : Microsoft.WindowsStore_8wekyb3d8bbwe' in result.stdout:
                try:
                    # 如果安装了 Microsoft Store，运行命令
                    subprocess.run(
                        ['powershell.exe', '-Command', 'Start-Process ms-windows-store://pdp/?ProductId=9PM860492SZD'], creationflags=subprocess.CREATE_NO_WINDOW)
                    return self.translator.translate("download_from_msstore_app_opened")
                except Exception as e:
                    return f"{self.translator.translate('download_from_msstore_app_error')}: {str(e)}"
            else:
                # 如果没有安装 Microsoft Store，打开指定的 URL
                webbrowser.open("https://www.microsoft.com/store/productid/9PM860492SZD")
                return self.translator.translate("download_from_msstore_site_opened")
        except Exception as e:
            return f"{self.translator.translate('download_from_msstore_site_error')}: {str(e)}"

    def install_for_all_users(self):
        # 打开文件选择对话框选择文件
        all_users_application_package_file_path = filedialog.askopenfilename(
            filetypes=[("Msix/MsixBundle", "*.msix;*.msixbundle"),
                       ("*", "*")])

        if not all_users_application_package_file_path:
            return self.translator.translate("install_for_all_users_no_file_selected")

        # 弹出提示框询问用户是否选择许可证文件
        response_for_all_users_license = messagebox.askyesnocancel(
            self.translator.translate("install_for_all_users_license_select_notice"),
            self.translator.translate("install_for_all_users_license_select")
        )

        all_users_dependency_package_paths = None
        if response_for_all_users_license:  # 使用许可证
            all_users_license_path = filedialog.askopenfilename(
                filetypes=[("License.xml", "*.xml"), ("*", "*")])
            if not all_users_license_path:
                return self.translator.translate("install_for_all_users_no_file_selected")
        elif response_for_all_users_license == None:
            return self.translator.translate("user_canceled")
        else:
            all_users_license_path = None

        # 弹出提示框询问用户是否选择依赖包
        response_for_all_users_dependency = messagebox.askyesnocancel(
            self.translator.translate("install_for_all_users_dependency_package_select_notice"),
            self.translator.translate("install_for_all_users_dependency_package_select")
        )

        if response_for_all_users_dependency:  # 选择依赖包
            all_users_dependency_package_paths = filedialog.askopenfilenames(
                filetypes=[("Msix", "*.msix"),
                           ("*", "*")])
            if not all_users_dependency_package_paths:
                return self.translator.translate("install_for_all_users_no_file_selected")
        elif response_for_all_users_dependency == None:
            return self.translator.translate("user_canceled")

        try:
            # 构建 Dism.exe 命令
            all_users_dism_command = ['Dism.exe', '/Online', '/Add-ProvisionedAppxPackage',
                                      f'/PackagePath:{all_users_application_package_file_path}']

            if all_users_license_path:  # 使用许可证文件
                all_users_dism_command.append(f'/LicensePath:{all_users_license_path}')
            else:  # 不使用许可证文件
                all_users_dism_command.append('/SkipLicense')

            if all_users_dependency_package_paths:  # 使用依赖包，若不使用则跳过
                for dependency_path in all_users_dependency_package_paths:
                    all_users_dism_command.append(f'/DependencyPackagePath:{dependency_path}')

            # 使用 Dism.exe 安装应用
            result = subprocess.run(all_users_dism_command, capture_output=True, text=True,
                                    creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode == 0:
                return self.translator.translate("install_for_all_users_success")
            else:
                return self.translator.translate("install_for_all_users_error") + f": {result.stderr}\n{result.stdout}"
        except Exception as e:
            return self.translator.translate("install_for_all_users_error") + f": {str(e)}"

    def install_for_current_user(self):
        # 打开文件选择对话框选择文件
        current_user_application_package_file_path = filedialog.askopenfilename(
            filetypes=[("Msix/MsixBundle", "*.msix;*.msixbundle"),
                       ("*", "*")])

        if not current_user_application_package_file_path:
            return self.translator.translate("install_for_current_user_no_file_selected")

        # 弹出提示框询问用户是否选择依赖包
        response_for_current_user_dependency = messagebox.askyesnocancel(
            self.translator.translate("install_for_current_user_dependency_package_select_notice"),
            self.translator.translate("install_for_current_user_dependency_package_select")
        )

        current_user_dependency_package_paths = None
        if response_for_current_user_dependency:  # 选择依赖包
            current_user_dependency_package_paths = filedialog.askopenfilenames(
                filetypes=[("Msix", "*.msix"),
                           ("*", "*")])
            if not current_user_dependency_package_paths:
                return self.translator.translate("install_for_current_user_no_file_selected")
        elif response_for_current_user_dependency == None:
            return self.translator.translate("user_canceled")

        try:
            # 构建 Add-AppxPackage 命令
            command = ['powershell.exe', '-Command',
                       f'Add-AppxPackage -Path "{current_user_application_package_file_path}"']
            if current_user_dependency_package_paths:  # 使用依赖包，若不使用则跳过
                dependency_paths = ",".join([f'"{additional_dependency_paths}"' for additional_dependency_paths in current_user_dependency_package_paths])
                command.append(f'-DependencyPath {dependency_paths}')

            # 执行 Add-AppxPackage 命令安装应用
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode == 0:
                return self.translator.translate("install_for_current_user_success")
            else:
                return self.translator.translate(
                    "install_for_current_user_error") + f": {result.stderr}\n{result.stdout}"
        except Exception as e:
            return self.translator.translate("install_for_current_user_error") + f": {str(e)}"

    def update_from_application_package(self):
        # 打开文件选择对话框选择文件
        update_application_package_file_path = filedialog.askopenfilename(
            filetypes=[("Msix/MsixBundle", "*.msix;*.msixbundle"),
                       ("*", "*")])

        if not update_application_package_file_path:
            return self.translator.translate("update_from_application_package_no_file_selected")

        # 弹出提示框询问用户是否选择依赖包
        response_for_update_dependency = messagebox.askyesnocancel(
            self.translator.translate("update_from_application_package_dependency_package_select_notice"),
            self.translator.translate("update_from_application_package_dependency_package_select")
        )

        update_dependency_package_paths = None
        if response_for_update_dependency:  # 选择依赖包
            update_dependency_package_paths = filedialog.askopenfilenames(
                filetypes=[("Msix", "*.msix"),
                           ("*", "*")])
            if not update_dependency_package_paths:
                return self.translator.translate("update_from_application_package_no_file_selected")
        elif response_for_update_dependency == None:
            return self.translator.translate("user_canceled")

        try:
            # 构建 Add-AppxPackage 命令
            command = ['powershell.exe', '-Command',
                       f'Add-AppxPackage -Path "{update_application_package_file_path}"']
            if update_dependency_package_paths:  # 使用依赖包，若不使用则跳过
                dependency_paths = ",".join([f'"{additional_dependency_paths}"' for additional_dependency_paths in
                                             update_dependency_package_paths])
                command.append(f'-DependencyPath {dependency_paths}')

            # 执行 Add-AppxPackage 命令安装应用
            result = subprocess.run(command, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)

            if result.returncode == 0:
                return self.translator.translate("update_from_application_package_success")
            else:
                return self.translator.translate(
                    "update_from_application_package_error") + f": {result.stderr}\n{result.stdout}"
        except Exception as e:
            return self.translator.translate("update_from_application_package_error") + f": {str(e)}"

    def install_from_appxmanifest(self):
        # 弹出警告提示框
        response = messagebox.askyesnocancel(
            self.translator.translate("install_from_appxmanifest_warn_title"),
            self.translator.translate("install_from_appxmanifest_warn")
        )

        if response is None or not response:
            return self.translator.translate("user_canceled")

        # 打开文件选择对话框选择文件
        appxmanifest_file_path = filedialog.askopenfilename(
            filetypes=[("Msix/MsixBundle", "*.msix;*.msixbundle"), ("*", "*")]
        )

        if not appxmanifest_file_path:
            return self.translator.translate("user_canceled")

        try:
            # 创建临时目录
            temp_appxmanifest_file_path = os.path.join(tempfile.gettempdir(), "MSPCManagerHelper")
            if not os.path.exists(temp_appxmanifest_file_path):
                os.makedirs(temp_appxmanifest_file_path)

            # 复制文件到临时目录并重命名为 .zip
            file_name = os.path.basename(appxmanifest_file_path)
            zip_file_path = os.path.join(temp_appxmanifest_file_path, file_name + ".zip")
            shutil.copyfile(appxmanifest_file_path, zip_file_path)

            # 解压文件
            pc_manager_unpacked_path = os.path.join(temp_appxmanifest_file_path, os.path.splitext(file_name)[0])
            shutil.unpack_archive(zip_file_path, pc_manager_unpacked_path)

            # 检测解压后的文件夹内是否还有 .msix 文件
            msix_files = [f for f in os.listdir(pc_manager_unpacked_path) if f.endswith('.msix')]
            if not msix_files:
                # 写入 exclude.txt
                exclude_file_path = os.path.join(temp_appxmanifest_file_path, "exclude.txt")
                with open(exclude_file_path, 'w') as exclude_file:
                    exclude_file.write("AppxMetadata\n")
                    exclude_file.write("[Content_Types].xml\n")
                    exclude_file.write("AppxBlockMap.xml\n")
                    exclude_file.write("AppxSignature.p7x\n")
            else:
                # 检查文件名中是否带有 x64 或 arm64
                x64_file = next((f for f in msix_files if 'x64' in f), None)
                arm64_file = next((f for f in msix_files if 'arm64' in f), None)
                if not x64_file and not arm64_file:
                    return self.translator.translate("install_from_appxmanifest_no_match_pc_manager_architecture")

                # 读取 PROCESSOR_ARCHITECTURE 的值
                processor_architecture = winreg.QueryValueEx(
                    winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                   r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
                    "PROCESSOR_ARCHITECTURE"
                )[0]

                if processor_architecture == "AMD64" and x64_file:
                    zip_file_path = os.path.join(temp_appxmanifest_file_path, x64_file + ".zip")
                    shutil.copyfile(os.path.join(pc_manager_unpacked_path, x64_file), zip_file_path)
                    shutil.unpack_archive(zip_file_path,
                                          os.path.join(temp_appxmanifest_file_path, os.path.splitext(x64_file)[0]))
                    pc_manager_unpacked_path = os.path.join(temp_appxmanifest_file_path, os.path.splitext(x64_file)[0])
                elif processor_architecture == "ARM64" and arm64_file:
                    zip_file_path = os.path.join(temp_appxmanifest_file_path, arm64_file + ".zip")
                    shutil.copyfile(os.path.join(pc_manager_unpacked_path, arm64_file), zip_file_path)
                    shutil.unpack_archive(zip_file_path,
                                          os.path.join(temp_appxmanifest_file_path, os.path.splitext(arm64_file)[0]))
                    pc_manager_unpacked_path = os.path.join(temp_appxmanifest_file_path,
                                                            os.path.splitext(arm64_file)[0])
                else:
                    shutil.rmtree(temp_appxmanifest_file_path)
                    return self.translator.translate("install_from_appxmanifest_no_match_architecture")

                # 写入 exclude.txt
                exclude_file_path = os.path.join(temp_appxmanifest_file_path, "exclude.txt")
                with open(exclude_file_path, 'w') as exclude_file:
                    exclude_file.write("AppxMetadata\n")
                    exclude_file.write("[Content_Types].xml\n")
                    exclude_file.write("AppxBlockMap.xml\n")
                    exclude_file.write("AppxSignature.p7x\n")

            # 将最后解压的文件夹复制到 %ProgramFiles% 下，除了 exclude.txt 列出的文件与文件夹
            program_files_path = os.path.join(os.environ['ProgramFiles'], os.path.basename(pc_manager_unpacked_path))
            if not os.path.exists(program_files_path):
                os.makedirs(program_files_path)

            with open(exclude_file_path, 'r') as exclude_file:
                exclude_list = exclude_file.read().splitlines()

            for root, dirs, files in os.walk(pc_manager_unpacked_path):
                relative_path = os.path.relpath(root, pc_manager_unpacked_path)
                if relative_path in exclude_list:
                    continue

                dest_dir = os.path.join(program_files_path, relative_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)

                for file in files:
                    if file in exclude_list:
                        continue
                    shutil.copyfile(os.path.join(root, file), os.path.join(dest_dir, file))

            # 修改 AppxManifest.xml 文件
            appxmanifest_path = os.path.join(program_files_path, "AppxManifest.xml")
            with open(appxmanifest_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            with open(appxmanifest_path, 'w', encoding='utf-8') as file:
                for line in lines:
                    if '<TargetDeviceFamily' in line and not line.strip().startswith('<!--'):
                        indent = line[:len(line) - len(line.lstrip())]
                        file.write(f"{indent}<!-- {line.strip()} -->\n")
                        file.write(
                            f"{indent}<TargetDeviceFamily Name=\"Windows.Universal\" MinVersion=\"10.0.17763.0\" MaxVersionTested=\"10.0.22621.0\"/>\n")
                    else:
                        file.write(line)

            # 弹出提示框询问用户是否选择依赖包
            response_for_dependency = messagebox.askyesnocancel(
                self.translator.translate("install_from_appxmanifest_dependency_package_select_notice"),
                self.translator.translate("install_from_appxmanifest_dependency_package_select")
            )

            if response_for_dependency:  # 选择依赖包
                dependency_package_paths = filedialog.askopenfilenames(
                    filetypes=[("Msix", "*.msix"), ("*", "*")])
                if not dependency_package_paths:
                    return self.translator.translate("install_from_appxmanifest_no_file_selected")

                for dependency_path in dependency_package_paths:
                    subprocess.run(
                        ['powershell.exe', '-Command', f'Add-AppxPackage -Path "{dependency_path}"'],
                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                    )

            # 注册 AppxManifest.xml
            subprocess.run(
                ['powershell.exe', '-Command', f'Add-AppxPackage -Register "{program_files_path}\\AppxManifest.xml"'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )

            # 询问是否注册服务
            response_for_service = messagebox.askyesno(
                self.translator.translate("install_from_appxmanifest_register_svc_notice"),
                self.translator.translate("install_from_appxmanifest_register_svc")
            )

            if response_for_service:
                # 检查服务 "PCManager Service Store" 是否存在
                service_check_store = subprocess.run(
                    ['powershell.exe', '-Command', 'Get-Service -Name "PCManager Service Store"'],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )

                # 检查服务 "PC Manager Service" 是否存在
                service_check_store_old = subprocess.run(
                    ['powershell.exe', '-Command', 'Get-Service -Name "PC Manager Service"'],
                    capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                )

                if service_check_store.returncode == 0 or service_check_store_old.returncode == 0:
                    messagebox.showwarning(
                        self.translator.translate("install_from_appxmanifest_svc_exists_warning"),
                        self.translator.translate("install_from_appxmanifest_svc_exists")
                    )
                else:
                    # 创建服务
                    service_create = subprocess.run(
                        ['sc.exe', 'create', 'PCManager Service Store', 'binPath=',
                         f'"{program_files_path}\\PCManager\\MSPCManagerService.exe"',
                         'DisplayName=', '"MSPCManager Service (Store)"', 'start=', 'auto'],
                        capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                    )

                    if service_create.returncode == 0:
                        # 设置服务描述
                        subprocess.run(
                            ['sc.exe', 'description', 'PCManager Service Store',
                             '"Microsoft PCManager Service For Store"'],
                            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        # 启动服务
                        subprocess.run(
                            ['sc.exe', 'start', 'PCManager Service Store'],
                            capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
                        )

            # 清理临时文件
            for file in os.listdir(temp_appxmanifest_file_path):
                file_path = os.path.join(temp_appxmanifest_file_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)

            return self.translator.translate("install_from_appxmanifest_success")
        except Exception as e:
            return f"{self.translator.translate('install_from_appxmanifest_error')}: {str(e)}"

    def install_wv2_runtime(self, app):
        wv2_installer_temp_dir = os.path.join(tempfile.gettempdir(), "MSPCManagerHelper")
        installer_path = os.path.join(wv2_installer_temp_dir, "MicrosoftEdgeWebView2Setup.exe")
        download_url = "https://go.microsoft.com/fwlink/p/?LinkId=2124703"

        try:
            # 检查临时目录是否存在
            if os.path.exists(wv2_installer_temp_dir):
                shutil.rmtree(wv2_installer_temp_dir)  # 删除临时目录

            # 创建临时目录
            os.makedirs(wv2_installer_temp_dir, exist_ok=True)

            # 下载文件
            response = requests.get(download_url)
            if response.status_code == 200:
                with open(installer_path, 'wb') as file:
                    file.write(response.content)
            else:
                return self.translator.translate("wv2_download_error")

            # 运行安装程序
            app.current_process = subprocess.Popen([installer_path, "/install"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = app.current_process.communicate()

            if app.cancelled:
                return self.translator.translate("wv2_installation_cancelled")

            if app.current_process.returncode == 0:
                return self.translator.translate("wv2_runtime_install_success")
            elif app.current_process.returncode == 2147747880:
                return f"{self.translator.translate('wv2_installer_exit_code')}: {app.current_process.returncode}\n{self.translator.translate('wv2_runtime_already_installed')}"
            elif app.current_process.returncode == 2147747596:
                return f"{self.translator.translate('wv2_installer_exit_code')}: {app.current_process.returncode}\n{self.translator.translate('wv2_installer_exit_code_0x8004070c')}"
            elif app.current_process.returncode == 2147942583:
                return f"{self.translator.translate('wv2_installer_exit_code')}: {app.current_process.returncode}\n{self.translator.translate('wv2_installer_exit_code_0x800700b7')}"
            else:
                return f"{self.translator.translate('wv2_installer_exit_code')}: {app.current_process.returncode}\n{self.translator.translate('wv2_installer_error')}"
        except Exception as e:
            return f"{self.translator.translate('wv2_download_error_info')}: {str(e)}"
        finally:
            # 删除临时目录
            if os.path.exists(wv2_installer_temp_dir):
                shutil.rmtree(wv2_installer_temp_dir)
            app.current_process = None
