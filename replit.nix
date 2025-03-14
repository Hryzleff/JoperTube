{pkgs}: {
  deps = [
    pkgs.libopus
    pkgs.libsodium
    pkgs.ffmpeg-full
    pkgs.postgresql
    pkgs.openssl
  ];
}
