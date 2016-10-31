import os
from datetime import datetime


def get_dependencies(odoo_addon_dir, moduleName):
    module_dir = os.path.join(odoo_addon_dir, moduleName, "__openerp__.py")
    if moduleName == '':
        return ''
    elif not os.path.exists(module_dir):
        print "The folder %s does not exist!" % module_dir
        return ''
    fp = open(module_dir)
    modules = text_read = ""
    while True:
        ch = fp.read(1)
        if not ch:
            break
        text_read = text_read.__add__(ch)
        if text_read.endswith('\'depends\''):
            while True:
                ch = fp.read(1)
                if ch == ':':
                    break
            while True:
                ch = fp.read(1)
                if ch == '[':
                    break
            while True:
                ch = fp.read(1)
                if ch != ']':
                    modules = modules.__add__(ch)
                else:
                    break
            fp.close()
            break

    temp = modules.split('\'')
    ret = []
    for i in temp:
        temp2 = i.split('\"')
        for j in temp2:
            tempfile = os.path.join(odoo_addon_dir, j)
            if not j.__contains__(',') and os.path.exists(tempfile):
                ret.append(j)

    ret = sorted(ret)
    return ret


########################################################################################################################
########################################################################################################################
###                             get the dependencies

def get_dependency_tree(odoo_addon_dir, auto_installable_modules, base_module):
    modules_needed = []
    modules_needed += auto_installable_modules
    modules_needed.append(base_module)
    for module in modules_needed:
        dependencies = get_dependencies(odoo_addon_dir, module)
        for dependency in dependencies:
            if not dependency in modules_needed:
                modules_needed.append(dependency)

    modules_needed = sorted(modules_needed)
    return modules_needed


########################################################################################################################
########################################################################################################################
###                             This part is to delete ALL non-dependencies!

def delete_folders(odoo_addon_dir, folder_list):
    for folder in folder_list:
        path = os.path.join(odoo_addon_dir, folder)
        os.system("sudo rm -r %s" % path)
        print "Done deleting."


########################################################################################################################
########################################################################################################################
###                 get deletable folders

def get_modules_to_delete(all_modules, modules_needed):
    to_delete = []
    for folder in all_modules:
        module_dir = os.path.join(odoo_addon_dir, folder, "__openerp__.py")
        if os.path.exists(module_dir):
            if not folder in modules_needed:
                to_delete.append(folder)
    return to_delete


########################################################################################################################
########################################################################################################################
###                         Log all deletions

def create_log_file(modules_to_delete):
    log_file = open("odoo_delete_log.txt", "a")
    log_file.writelines("#" * 80)
    log_file.writelines("\n")
    log_file.writelines("%s\n" % datetime.now())
    log_file.writelines("The following %d modules were deleted:\n" % len(modules_to_delete))
    for module in modules_to_delete:
        log_file.writelines(module)
        log_file.writelines("\n")   
    log_file.writelines("\n")
    log_file.close()


########################################################################################################################
########################################################################################################################
###                                 check if module's auto_install is set to 'True'

def is_auto_installable(odoo_addon_dir, moduleName):
    module_dir = os.path.join(odoo_addon_dir, moduleName, "__openerp__.py")
    if moduleName == '':
        return ''
    elif not os.path.exists(module_dir):
        print "The folder %s does not exist!" % module_dir
        return ''
    fp = open(module_dir)
    is_auto = text_read = ""
    while True:
        ch = fp.read(1)
        if not ch:
            break
        text_read = text_read.__add__(ch)
        if text_read.endswith('\'auto_install\''):
            while True:
                ch = fp.read(1)
                if ch == ':' or ch.isspace() or ch.isalpha():
                    is_auto = is_auto.__add__(ch)
                else:
                    break
            fp.close()
            break
    if is_auto.__contains__("True"):
        return True
    else:
        return False


########################################################################################################################
########################################################################################################################
###                                 Filter auto_installables.

def filter_auto_installables(odoo_addon_dir, direct_dependencies, auto_installables):
    filtered_modules = []
    for module in auto_installables:
        small_list = get_dependency_tree(odoo_addon_dir, auto_installable_modules=[], base_module=module)
        if subset(direct_dependencies, small_list):
            filtered_modules.append(module)
    return filtered_modules


########################################################################################################################
########################################################################################################################
###                                 find all modules with auto_install set to 'True'

def get_auto_installables(odoo_addon_dir, module_list):
    auto_installables = []
    for module in module_list:
        if is_auto_installable(odoo_addon_dir, module):
            auto_installables.append(module)
    return auto_installables


########################################################################################################################
########################################################################################################################
###                                     Is one list a subset of another?

def subset(big_list, small_list):
    if len(small_list) > len(big_list):
        return False
    for item in small_list:
        if not (item in big_list):
            return False
    return True


########################################################################################################################
########################################################################################################################
###                 MAIN

odoo_addon_dir = '/home/faison/odoo/addons'  ## hard-coded for Faison's machine
odoo_addon_dir = raw_input("Enter the absolute path to your odoo addons folder: ")
base_module = raw_input("Enter the name of the base module folder: ")
all_modules = os.listdir(odoo_addon_dir)
auto_installable_modules = get_auto_installables(odoo_addon_dir, all_modules)
modules_needed = get_dependency_tree(odoo_addon_dir, auto_installable_modules=[], base_module=base_module)
auto_installable_modules = filter_auto_installables(odoo_addon_dir, modules_needed, auto_installable_modules)
modules_needed = get_dependency_tree(odoo_addon_dir, auto_installable_modules, base_module)
modules_to_delete = get_modules_to_delete(all_modules, modules_needed)

print "Auto-installable modules: "
print auto_installable_modules
y = raw_input("\nPress any key to continue...")
print "Dependencies of current module: "
print modules_needed
y = raw_input("\nPress any key to continue...")
print "All modules available: "
print sorted(all_modules)
y = raw_input("\nPress any key to continue...")
print "The following folders are to be deleted: \n%s" % modules_to_delete
# Pick whether or not to delete folders.
y = "X"
while not y in ("n", "N", "y", "Y"):
    y = raw_input("\nDo you want to delete ALL non-dependencies to the above module? Y/N :")
    if y == 'n' or y == 'N':
        pass
    elif y == "y" or y == "Y":
        delete_folders(odoo_addon_dir, modules_to_delete)
        create_log_file(modules_to_delete)
