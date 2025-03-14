{pkgs}: {
  deps = [
    pkgs.libsodium
    pkgs.ffmpeg-full
    pkgs.postgresql
    pkgs.openssl
  ];
}
