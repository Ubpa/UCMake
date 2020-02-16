#include <test_03_dll/servant.h>

#include <iostream>

using namespace std;

void Servant::Speak() {
	cout << "Servant::Speak: ohayo master" << endl;
}

DLL_SPEC void servant_speak() {
	Servant servant;
	cout << "servant_speak():" << endl
		<< "\t";
	servant.Speak();
}
