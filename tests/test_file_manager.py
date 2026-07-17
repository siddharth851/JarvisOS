import os
import shutil
import tempfile

from jarvis.services.file_manager import FileManager


def test_create_open_delete_file():
    fm = FileManager()
    with tempfile.TemporaryDirectory() as td:
        p = os.path.join(td, "notes.txt")
        resp = fm.create_file(p)
        assert resp["status"] == "success"

        # write content
        with open(p, "w") as f:
            f.write("hello")

        open_resp = fm.open_file(p)
        assert open_resp["status"] == "success"
        assert open_resp["data"]["content"] == "hello"

        del_resp = fm.delete(p)
        assert del_resp["status"] == "success"


def test_create_and_open_folder():
    fm = FileManager()
    with tempfile.TemporaryDirectory() as td:
        folder = os.path.join(td, "AI Projects")
        resp = fm.create_folder(folder)
        assert resp["status"] == "success"

        open_resp = fm.open_folder(folder)
        assert open_resp["status"] == "success"
        assert isinstance(open_resp["data"]["items"], list)


def test_rename_move_copy():
    fm = FileManager()
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "a.txt")
        with open(src, "w") as f:
            f.write("x")

        dst = os.path.join(td, "b.txt")
        r = fm.rename(src, dst)
        assert r["status"] == "success"
        assert os.path.exists(dst)

        # move
        dest_dir = os.path.join(td, "sub")
        m = fm.move(dst, os.path.join(dest_dir, "b.txt"))
        assert m["status"] == "success"
        assert os.path.exists(os.path.join(dest_dir, "b.txt"))

        # copy file
        copy_dst = os.path.join(td, "copy_of_b.txt")
        c = fm.copy(os.path.join(dest_dir, "b.txt"), copy_dst)
        assert c["status"] == "success"
        assert os.path.exists(copy_dst)

        # copy folder
        folder_src = os.path.join(td, "folder_src")
        os.makedirs(folder_src)
        with open(os.path.join(folder_src, "inner.txt"), "w") as f:
            f.write("x")
        folder_copy = os.path.join(td, "folder_copy")
        c2 = fm.copy(folder_src, folder_copy)
        assert c2["status"] == "success"
        assert os.path.exists(os.path.join(folder_copy, "inner.txt"))
