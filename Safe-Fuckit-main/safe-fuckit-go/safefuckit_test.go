package safefuckit

import (
	"testing"
)

func TestBasicProtection(t *testing.T) {
	state := map[string]interface{}{
		"counter": 0,
		"name":    "hello",
	}

	guard := New(state)
	err := guard.Do(func() {
		state["counter"] = 1
		state["name"] = "world"
		panic("oops!")
	})

	if err == nil {
		t.Fatal("expected error")
	}

	if state["counter"] != 0 {
		t.Errorf("expected counter to rollback to 0, got %v", state["counter"])
	}
	if state["name"] != "hello" {
		t.Errorf("expected name to rollback to 'hello', got %v", state["name"])
	}
}

func TestNoPanic(t *testing.T) {
	state := map[string]interface{}{
		"counter": 0,
	}

	guard := New(state)
	err := guard.Do(func() {
		state["counter"] = 42
	})

	if err != nil {
		t.Fatalf("expected no error, got %v", err)
	}
	if state["counter"] != 42 {
		t.Errorf("expected counter to be 42, got %v", state["counter"])
	}
}

func TestEnterExit(t *testing.T) {
	state := map[string]interface{}{
		"value": "original",
	}

	guard := New(state)
	guard.Enter()
	state["value"] = "changed"
	guard.Exit()

	if state["value"] != "changed" {
		t.Errorf("without a panic, state should remain changed: got %v", state["value"])
	}
}
