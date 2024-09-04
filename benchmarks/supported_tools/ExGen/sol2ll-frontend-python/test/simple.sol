pragma solidity ^0.4.22;

contract SimpleAuction {
    address public beneficiary = "0x1234567890123456789012345678901234567890";
    uint public auctionEnd = 0;
    address public highestBidder;
    uint public highestBid;
    mapping(address => uint) pendingReturns;
    address[] accounts;
    bool ended;

    struct MyStructName {
        address addr;
        uint256 count;
    }
    MyStructName haha;

    enum SomeData {DEFAULT,ONE,TWO}
    SomeData someData;

    event HighestBidIncreased(address bidder, uint amount);
    event AuctionEnded(address winner, uint amount);

    constructor(
        uint _biddingTime,
        address _beneficiary
    ) public {
        beneficiary = _beneficiary;
        auctionEnd = now + _biddingTime;
    }

    function(uint a, uint b) public {}
    function(SimpleAuction a) public {}

    function bid() public payable {
        require(
            now <= auctionEnd,
            "Auction already ended."
        );

        require(
            msg.value > highestBid,
            "There already is a higher bid."
        );

        if (highestBid != 0) {
            pendingReturns[highestBidder] += highestBid;
        }
        highestBidder = msg.sender;
        highestBid = msg.value;
        emit HighestBidIncreased(msg.sender, msg.value);
    }

    /// Withdraw a bid that was overbid.
    function withdraw() public returns (bool) {
        uint amount = pendingReturns[msg.sender];
        if (amount > 0) {
            pendingReturns[msg.sender] = 0;

            if (!msg.sender.send(amount)) {
                pendingReturns[msg.sender] = amount;
                return false;
            }
        }
        return true;
    }

    modifier loli  () {

    }

    function lol() public  {
        return pendingReturns[msg.sender];
    }

    function auctionEnd() public {
        require(now >= auctionEnd, "Auction not yet ended.");
        require(!ended, "auctionEnd has already been called.");
        ended = true;
        emit AuctionEnded(highestBidder, highestBid);
        beneficiary.transfer(highestBid);
    }
}