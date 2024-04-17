import h5py
import cv2
import os
import os.path as osp
import numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-p', '--path', type=str, required=True, help="path to h5 result file")
parser.add_argument('-d', '--frm-dir', type=str, required=True, help="path to frame directory")
parser.add_argument('-i', '--idx', type=int, default=0, help="which key to choose")
parser.add_argument('--fps', type=int, default=30, help="frames per second")
parser.add_argument('--width', type=int, default=640, help="frame width")
parser.add_argument('--height', type=int, default=480, help="frame height")
parser.add_argument('--save-dir', type=str, default='log', help="directory to save")
parser.add_argument('--save-name', type=str, default='summary.mp4', help="video name to save (ends with .mp4)")
args = parser.parse_args()

def frm2video(frm_dir, summary, vid_writer):
    
    """
    Converts a sequence of frames to a video summary.

    Args:
        frm_dir (str): Path to the directory containing frame images.
        summary (numpy.ndarray): Binary array indicating whether each frame should be included in the summary.
        vid_writer (cv2.VideoWriter): Video writer object to write the summary video.
    """

    for idx, val in enumerate(summary):
        if val == 1:
            frm_name = f'frame_{idx+1}.jpg'
            frm_path = osp.join(frm_dir, frm_name)
            if not osp.exists(frm_path):
                print(f"Warning: Frame {frm_name} not found in {frm_dir}")
                continue
            frm = cv2.imread(frm_path)
            if frm is None or frm.size == 0:
                print(f"Warning: Unable to read frame {frm_name}")
                continue
            frm = cv2.resize(frm, (args.width, args.height))
            vid_writer.write(frm)
            frm_path = osp.join(frm_dir, frm_name)
            if not osp.exists(frm_path):
                print(f"Warning: Frame {frm_name} not found in {frm_dir}")
                continue
            frm = cv2.imread(frm_path)
            if frm is None or frm.size == 0:
                print(f"Warning: Unable to read frame {frm_name}")
                continue
            frm = cv2.resize(frm, (args.width, args.height))
            vid_writer.write(frm)

if __name__ == '__main__':
    if not osp.exists(args.save_dir):
        os.makedirs(args.save_dir)  # Use makedirs to create intermediate directories if necessary
    vid_writer = cv2.VideoWriter(
        osp.join(args.save_dir, args.save_name), 
        cv2.VideoWriter_fourcc(*'mp4v'),  # Change the codec to 'mp4v'
        args.fps, (args.width, args.height)
    )
    h5_res = h5py.File(args.path, 'r')
    keys_list = list(h5_res.keys())
    key = keys_list[args.idx]
    summary = h5_res[key]['machine_summary'][...]
    h5_res.close()
    frm2video(args.frm_dir, summary, vid_writer)
    vid_writer.release()