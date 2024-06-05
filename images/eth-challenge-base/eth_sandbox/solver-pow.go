package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"math/rand"
	"time"
)

func main() {
	rand.Seed(time.Now().UnixNano())

	x := 100000000 + rand.Int63n(200000000000)

	for i := x; i < x+20000000000; i++ {
		ticket := fmt.Sprintf("%d", i)

		m := sha256.New()
		m.Write([]byte(ticket))
		digest1 := m.Sum(nil)

		m = sha256.New()
		m.Write(append(digest1, []byte(ticket)...))
		digest2 := m.Sum(nil)
		hexdigest2 := hex.EncodeToString(digest2)

		if len(hexdigest2) >= 7 && hexdigest2[:7] == "0000000" {
			fmt.Println(i)
			break
		}
	}
}
