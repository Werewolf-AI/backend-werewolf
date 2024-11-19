{pkgs}: {
  deps = [
    pkgs.python312Packages.gunicorn
    pkgs.lsof
    pkgs.unzip
    pkgs.wget
    pkgs.vim
  ];
}
