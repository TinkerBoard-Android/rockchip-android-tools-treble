// Copyright 2020 Google LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     https://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// hacksawd is a privileged daemon that manages the mounts
package main

import (
	"io/ioutil"
	"net"
	"net/http"
	"net/rpc"
	"os"
	"path"
	"strconv"

	"android.googlesource.com/platform/tools/treble.git/hacksaw/bind"
)

func main() {
	if os.Getenv("LISTEN_PID") != strconv.Itoa(os.Getpid()) {
		panic("Unexpected PID")
	}

	if os.Getenv("LISTEN_FDS") != strconv.Itoa(1) {
		panic("Unexpected number of socket fds")
	}

	// systemd will always provide the socket in this file descriptor
	//TODO: this directory is sometimes leaked
	dir, err := ioutil.TempDir("", "hacksawd")
	if err != nil {
		panic(err)
	}
	defer os.RemoveAll(dir)
	const socketFD = 3
	socketFile := os.NewFile(socketFD, path.Join(dir, "hacksawd.sock"))

	listener, err := net.FileListener(socketFile)
	if err != nil {
		panic(err)
	}

	binder := bind.NewLocalPathBinder()
	server := bind.NewServer(binder)
	if err = rpc.Register(server); err != nil {
		panic(err)
	}
	rpc.HandleHTTP()
	http.Serve(listener, nil)
}
