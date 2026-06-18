package safefuckit

import (
	"fmt"
	"log"
	"reflect"
	"runtime"
	"strings"
)

type SafeFuckIt struct {
	exTypes      []reflect.Type
	target       map[string]interface{}
	snapshot     map[string]interface{}
}

type Option func(*SafeFuckIt)

func WithExTypes(types ...interface{}) Option {
	return func(s *SafeFuckIt) {
		for _, t := range types {
			s.exTypes = append(s.exTypes, reflect.TypeOf(t))
		}
	}
}

func New(target map[string]interface{}, opts ...Option) *SafeFuckIt {
	s := &SafeFuckIt{
		exTypes: []reflect.Type{reflect.TypeOf((*error)(nil)).Elem()},
		target:  target,
	}
	for _, opt := range opts {
		opt(s)
	}
	return s
}

func (s *SafeFuckIt) takeSnapshot() {
	if s.target == nil {
		return
	}
	snapshot := make(map[string]interface{}, len(s.target))
	for k, v := range s.target {
		if strings.HasPrefix(k, "__") {
			continue
		}
		rv := reflect.ValueOf(v)
		if rv.Kind() == reflect.Func {
			continue
		}
		snapshot[k] = deepCopy(v)
	}
	s.snapshot = snapshot
}

func (s *SafeFuckIt) handleException(r interface{}) {
	log.Printf("[safe_fuckit] Exception isolated successfully!")
	log.Printf("   - Reason  : %T: %v", r, r)

	pc, file, line, ok := runtime.Caller(3)
	if ok {
		fn := runtime.FuncForPC(pc)
		funcName := fn.Name()
		log.Printf("   - Location: %s (%s:%d)", funcName, file, line)
	} else {
		log.Printf("   - Location: unknown")
	}

	if s.target != nil && s.snapshot != nil {
		log.Printf("[safe_fuckit] Data pollution risk detected. Rolling back variables to safe state.")
		for k := range s.target {
			if !strings.HasPrefix(k, "__") {
				if _, exists := s.snapshot[k]; !exists {
					rv := reflect.ValueOf(s.target[k])
					if rv.Kind() != reflect.Func {
						delete(s.target, k)
					}
				}
			}
		}
		for k, v := range s.snapshot {
			s.target[k] = v
		}
	}
}

func (s *SafeFuckIt) isMatch(r interface{}) bool {
	if r == nil {
		return false
	}
	err, ok := r.(error)
	if !ok {
		return true
	}
	errType := reflect.TypeOf(err)
	for _, et := range s.exTypes {
		if et == reflect.TypeOf((*error)(nil)).Elem() {
			return true
		}
		if errType == et || (et.Kind() == reflect.Interface && errType.Implements(et)) {
			return true
		}
	}
	return false
}

func (s *SafeFuckIt) Do(fn func()) (err error) {
	s.takeSnapshot()
	defer func() {
		if r := recover(); r != nil {
			if s.isMatch(r) {
				s.handleException(r)
				err = fmt.Errorf("safe_fuckit: %v", r)
			} else {
				panic(r)
			}
		}
	}()
	fn()
	return nil
}

func (s *SafeFuckIt) Enter() *SafeFuckIt {
	s.takeSnapshot()
	return s
}

func (s *SafeFuckIt) Exit() {
	s.snapshot = nil
}

func deepCopy(v interface{}) interface{} {
	if v == nil {
		return nil
	}
	rv := reflect.ValueOf(v)
	switch rv.Kind() {
	case reflect.Slice:
		if rv.IsNil() {
			return nil
		}
		result := reflect.MakeSlice(rv.Type(), rv.Len(), rv.Cap())
		reflect.Copy(result, rv)
		return result.Interface()
	case reflect.Map:
		if rv.IsNil() {
			return nil
		}
		result := reflect.MakeMap(rv.Type())
		for _, key := range rv.MapKeys() {
			result.SetMapIndex(key, reflect.ValueOf(deepCopy(rv.MapIndex(key).Interface())))
		}
		return result.Interface()
	default:
		return v
	}
}
