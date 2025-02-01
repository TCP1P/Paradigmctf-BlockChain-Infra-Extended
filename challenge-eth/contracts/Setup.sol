// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

contract Setup {
    bool private solved;

    constructor() payable {
    }
    function solve() public {
        solved = true;
    }

    function isSolved() external view returns (bool) {
        return solved;
    }
}
