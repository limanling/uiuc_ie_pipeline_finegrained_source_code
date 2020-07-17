#import tqdm
import os
import shutil

#####
def runner(out_folder_path):
    # shutil.rmtree(os.path.join(os.path.dirname(os.path.realpath(__file__)), 'intermediate_files/'))
    if os.path.exists(out_folder_path):
        shutil.rmtree(out_folder_path)
    os.makedirs(out_folder_path, exist_ok=True)
    # cwd_path = os.path.dirname(os.path.realpath(__file__))
    # os.chdir(os.path.join(cwd_path, 'intermediate_files/'))
    # for root, dirs, files in os.walk(".", topdown = False):
    #   for file in files:
    #      os.remove(os.path.join(root, file))
    # os.chdir(cwd_path)

#####
if __name__ == "__main__":
    out_folder_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'intermediate_files/')
    runner(out_folder_path)
    # cwd_path = os.path.dirname(os.path.realpath(__file__)) # os.getcwd()
    # os.chdir(os.path.join(cwd_path, 'intermediate_files/'))
    # for root, dirs, files in os.walk(".", topdown = False):
    #   for file in files:
    #      os.remove(os.path.join(root, file))
    # os.chdir(cwd_path)
