pragma solidity ^0.6.0;

contract Test {
    struct Transaction {
        address to;
        uint amount;
    }

    mapping(bytes32 => Transaction) transactions;

    address owner;

    function set_owner(address new_owner) public {
        owner = new_owner;
    }

    function new_transaction(address to, uint amount) public returns (bytes32) {
        bytes32 token = keccak256(abi.encodePacked(to, amount));
        Transaction storage t = transactions[token];
        t.to = to;
        t.amount += amount;
        return token;
    }

    function approve(bytes32 token) public {
        require(
            owner == msg.sender,
            "Only the owner can approve transactions."
        );
        Transaction storage t = transactions[token];
        address payable recipient = payable(t.to); // Explicitly cast to payable
        recipient.transfer(t.amount);
        delete transactions[token];
    }

    receive() external payable {}
}
